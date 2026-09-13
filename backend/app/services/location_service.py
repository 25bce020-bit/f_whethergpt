import os
import re

import httpx

from app.services.cache_service import get_or_load


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
LOCATION_TTL = int(os.getenv("OPEN_METEO_LOCATION_CACHE_TTL", "86400"))


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
    params = {
        "name": name,
        "count": 10,
        "language": "en",
        "format": "json",
    }

    async def load():
        async with httpx.AsyncClient() as client:
            response = await client.get(GEOCODING_URL, params=params, timeout=10.0)
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

    # Prefer Indian locations for this India-focused project
    india_results = [
        result
        for result in results
        if str(result.get("country_code", "")).upper() == "IN"
    ]

    if india_results:
        return india_results

    return results
