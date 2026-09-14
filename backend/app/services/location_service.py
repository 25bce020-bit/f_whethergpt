import os
import re

import httpx

from app.services.cache_service import get_or_load


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
LOCATION_TTL = int(os.getenv("OPEN_METEO_LOCATION_CACHE_TTL", "86400"))

# Open-Meteo's broad "Goa" lookup currently omits Goa, India and returns
# unrelated places such as Genoa. Keep this narrowly scoped canonical alias in
# the existing resolver rather than allowing a weather request to silently use
# another country. Coordinates represent Panaji, the state capital.
INDIA_LOCATION_ALIASES = {
    "goa": {
        "name": "Goa",
        "country": "India",
        "country_code": "IN",
        "admin1": "Goa",
        "latitude": 15.4909,
        "longitude": 73.8278,
    },
}


def normalize_location_name(name: str | None) -> str | None:
    """
    Clean a location candidate before sending it to the geocoding service.

    This is intentionally conservative. It removes common LLM extraction
    mistakes without trying to guess or rewrite legitimate place names.
    """
    if not name:
        return None

    cleaned = str(name).strip()

    # Remove wrapping quotes/backticks sometimes returned by an LLM.
    cleaned = cleaned.strip("\"'`")

    # Collapse repeated whitespace.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Remove common leading prepositions if the model included them.
    cleaned = re.sub(
        r"^(?:in|at|near|around|from|to)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Fix sentence-boundary contamination such as:
    # "Ahmedabad. Is tomorrow suitable?"
    # becoming "ahmedabad. is"
    #
    # We only do this when the text after the period looks like the
    # beginning of a new sentence. This avoids breaking legitimate
    # names such as "St. Louis".
    cleaned = re.sub(
        r"\.\s+(?:is|are|was|were|will|can|could|should|would|"
        r"do|does|did|may|might|has|have|what|how|when|where|why|"
        r"which|any)\b.*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove trailing punctuation.
    cleaned = cleaned.rstrip(".,;:!?")

    # Collapse whitespace one final time.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return None

    return cleaned


def normalize_location_name(name: str | None) -> str | None:
    """Remove common query glue without changing the centralized geocoding path."""
    if not name:
        return None
    normalized = " ".join(str(name).strip().split())
    # A malformed extractor can include the next sentence ("Ahmedabad. Is").
    # Location names sent to this service are a single geocoding query, so the
    # first sentence is the safe canonical candidate.
    normalized = re.split(r"[.?!]", normalized, maxsplit=1)[0].strip()
    normalized = re.sub(r"[?.!,;:]+$", "", normalized).strip()
    # English and Indian-language postpositions which may trail a city returned
    # by an LLM or fallback parser (for example, "Ahmedabad mein").
    normalized = re.sub(r"\s+(?:in|at|for|mein|me|में|मा(?:ं|ँ)|માં|मध्ये|இல்)$", "", normalized, flags=re.IGNORECASE)
    return normalized or None


async def search_location(name: str):
    """
    Search Open-Meteo for a location.

    The location is normalized here as a final safety layer so every caller
    benefits from the same cleanup.
    """
    name = normalize_location_name(name)

    if not name:
        return []

    params = {
        "name": name,
        "count": 10,
        "language": "en",
        "format": "json",
    }

    async def load():
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GEOCODING_URL,
                params=params,
                timeout=10.0,
            )

        response.raise_for_status()
        return response.json()

    normalized_name = " ".join(name.split()).casefold()

    cached = await get_or_load(
        f"open_meteo:location:{normalized_name}",
        "Open-Meteo geocoding",
        LOCATION_TTL,
        load,
    )

    data = cached["data"]
    results = data.get("results", [])

    if not results:
        return []

    # Prefer Indian locations when available.
    india_results = [
        result
        for result in results
        if str(result.get("country_code", "")).upper() == "IN"
    ]

    if india_results:
        return india_results

    # Only use a canonical Indian alias when the provider supplied no Indian
    # candidate at all. The normal provider-backed resolution remains primary.
    if normalized_name in INDIA_LOCATION_ALIASES:
        return [INDIA_LOCATION_ALIASES[normalized_name]]

    return results
