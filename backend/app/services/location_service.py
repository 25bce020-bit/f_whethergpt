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

TEMPORAL_PHRASES_RE = re.compile(
    r"^(?:the\s+)?(?:next|last|past|upcoming|coming|this|previous)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|few|couple\s+of)?\s*(?:hours?|hrs?|days?|weeks?|months?|years?|morning|afternoon|evening|night|weekend)\b"
    r"|^(?:next|last|this)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"|^(?:today|tomorrow|yesterday|tonight|now|currently|right\s+now|day\s+after\s+tomorrow)\b"
    r"|\b(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?)\b"
    r"|^(?:what|when|how|where|which|why|is|will|can|could|would|should|do|does|did)\b"
    r"|^(?:forecast|weather|rain|temperature|temp|climate|warning|alert|condition|conditions)\b",
    re.IGNORECASE,
)


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

    # Split on punctuation sentences
    cleaned = re.split(r"[.?!]", cleaned, maxsplit=1)[0].strip()

    # Remove common leading prepositions if the model included them.
    cleaned = re.sub(
        r"^(?:in|at|near|around|from|to|of|for)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Trailing punctuation
    cleaned = re.sub(r"[?.!,;:]+$", "", cleaned).strip()

    # English and Indian-language postpositions which may trail a city returned
    # by an LLM or fallback parser (for example, "Ahmedabad mein").
    cleaned = re.sub(
        r"\s+(?:in|at|for|mein|me|में|मा(?:ं|ँ)|માં|मध्ये|இல்)$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Collapse whitespace one final time.
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return None

    # Disallow temporal phrases from being interpreted as a location
    if TEMPORAL_PHRASES_RE.search(cleaned):
        return None

    return cleaned


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
