import os

import httpx

from app.services.cache_service import get_or_load


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
LOCATION_TTL = int(os.getenv("OPEN_METEO_LOCATION_CACHE_TTL", "86400"))


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
