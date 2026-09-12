import os

import httpx

from app.services.cache_service import get_or_load


HISTORICAL_TTL = int(os.getenv("OPEN_METEO_HISTORICAL_CACHE_TTL", "86400"))


async def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> dict:

    historical_url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max"
        ],
        "timezone": "auto"
    }

    async def load():
        async with httpx.AsyncClient() as client:
            response = await client.get(historical_url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()

    key = f"open_meteo:historical:{latitude:.4f}:{longitude:.4f}:{start_date}:{end_date}"
    cached = await get_or_load(key, "Open-Meteo historical weather", HISTORICAL_TTL, load)
    return cached["data"]


def format_historical_weather(data: dict) -> list:

    daily = data["daily"]

    historical = []

    for i in range(len(daily["time"])):

        historical.append({
            "date": daily["time"][i],
            "weather_code": daily["weather_code"][i],
            "temperature_max_c": daily["temperature_2m_max"][i],
            "temperature_min_c": daily["temperature_2m_min"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "wind_speed_max_kmh": daily["wind_speed_10m_max"][i]
        })

    return historical
def calculate_average_temperature(historical: list) -> float | None:

    temperatures = []

    for day in historical:
        max_temp = day.get("temperature_max_c")
        min_temp = day.get("temperature_min_c")

        if max_temp is not None and min_temp is not None:
            average = (max_temp + min_temp) / 2
            temperatures.append(average)

    if not temperatures:
        return None

    return round(sum(temperatures) / len(temperatures), 2)
