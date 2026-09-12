import os

import httpx

from app.services.cache_service import get_or_load


GFS_API_URL = "https://api.open-meteo.com/v1/gfs"
GFS_TTL = int(os.getenv("GFS_CACHE_TTL", "3600"))


async def get_gfs_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 7,
):
    """
    Retrieve global NCEP GFS forecast data.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_gusts_10m,"
            "wind_direction_10m,"
            "cloud_cover,"
            "surface_pressure"
        ),
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum,"
            "wind_speed_10m_max,"
            "wind_gusts_10m_max"
        ),
        "timezone": "Asia/Kolkata",
        "forecast_days": forecast_days,
    }

    async def load():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(GFS_API_URL, params=params)
        response.raise_for_status()
        return response.json()

    key = f"gfs:{latitude:.4f}:{longitude:.4f}:{forecast_days}"
    cached = await get_or_load(key, "NCEP GFS", GFS_TTL, load)
    return cached["data"]


def format_gfs_forecast(data: dict) -> dict:
    """
    Convert raw GFS response into a cleaner structure
    for WeatherGPT.
    """

    hourly = data.get("hourly", {})
    daily = data.get("daily", {})

    hourly_times = hourly.get("time", [])

    hourly_forecast = []

    for index, timestamp in enumerate(hourly_times):

        hourly_forecast.append(
            {
                "time": timestamp,
                "temperature_c": _get_value(
                    hourly.get("temperature_2m"),
                    index,
                ),
                "humidity_percent": _get_value(
                    hourly.get("relative_humidity_2m"),
                    index,
                ),
                "apparent_temperature_c": _get_value(
                    hourly.get("apparent_temperature"),
                    index,
                ),
                "precipitation_mm": _get_value(
                    hourly.get("precipitation"),
                    index,
                ),
                "rain_mm": _get_value(
                    hourly.get("rain"),
                    index,
                ),
                "weather_code": _get_value(
                    hourly.get("weather_code"),
                    index,
                ),
                "wind_speed_kmh": _get_value(
                    hourly.get("wind_speed_10m"),
                    index,
                ),
                "wind_gusts_kmh": _get_value(
                    hourly.get("wind_gusts_10m"),
                    index,
                ),
                "wind_direction_degrees": _get_value(
                    hourly.get("wind_direction_10m"),
                    index,
                ),
                "cloud_cover_percent": _get_value(
                    hourly.get("cloud_cover"),
                    index,
                ),
                "surface_pressure_hpa": _get_value(
                    hourly.get("surface_pressure"),
                    index,
                ),
            }
        )

    daily_times = daily.get("time", [])

    daily_forecast = []

    for index, forecast_date in enumerate(daily_times):

        daily_forecast.append(
            {
                "date": forecast_date,
                "temperature_max_c": _get_value(
                    daily.get("temperature_2m_max"),
                    index,
                ),
                "temperature_min_c": _get_value(
                    daily.get("temperature_2m_min"),
                    index,
                ),
                "precipitation_mm": _get_value(
                    daily.get("precipitation_sum"),
                    index,
                ),
                "wind_speed_max_kmh": _get_value(
                    daily.get("wind_speed_10m_max"),
                    index,
                ),
                "wind_gusts_max_kmh": _get_value(
                    daily.get("wind_gusts_10m_max"),
                    index,
                ),
                "weather_code": _get_value(
                    daily.get("weather_code"),
                    index,
                ),
            }
        )

    return {
        "model": "NCEP GFS",
        "provider": "NOAA",
        "hourly": hourly_forecast,
        "daily": daily_forecast,
    }


def _get_value(values, index):
    """
    Safely retrieve a value from an API array.
    """

    if not values:
        return None

    if index >= len(values):
        return None

    return values[index]
