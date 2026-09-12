import os

import httpx

from app.services.cache_service import get_or_load


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
CURRENT_TTL = int(os.getenv("OPEN_METEO_CURRENT_CACHE_TTL", "300"))
FORECAST_TTL = int(os.getenv("OPEN_METEO_FORECAST_CACHE_TTL", "900"))
HOURLY_TTL = int(os.getenv("OPEN_METEO_HOURLY_CACHE_TTL", "300"))


def _coordinates_key(latitude: float, longitude: float) -> str:
    return f"{latitude:.4f}:{longitude:.4f}"


async def get_current_weather(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_direction_10m"
        ),
        "timezone": "auto",
    }

    async def load():
        async with httpx.AsyncClient() as client:
            response = await client.get(OPEN_METEO_URL, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()

    cached = await get_or_load(
        f"open_meteo:current:{_coordinates_key(latitude, longitude)}",
        "Open-Meteo current weather",
        CURRENT_TTL,
        load,
    )
    return cached["data"]
def format_current_weather(data: dict) -> dict:
    current = data["current"]

    weather_code = current["weather_code"]

    return {
        "time": current["time"],
        "temperature_c": current["temperature_2m"],
        "feels_like_c": current["apparent_temperature"],
        "humidity_percent": current["relative_humidity_2m"],
        "precipitation_mm": current["precipitation"],
        "weather_code": weather_code,
        "condition": get_weather_condition(weather_code),
        "wind_speed_kmh": current["wind_speed_10m"],
        "wind_direction_degrees": current["wind_direction_10m"],
        "timezone": data["timezone"],
    }
def get_weather_condition(code: int) -> str:
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return weather_codes.get(code, "Unknown weather condition")
async def get_forecast(latitude: float, longitude: float):
    forecast_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ],
        "forecast_days": 7,
        "timezone": "auto",
    }

    async def load():
        async with httpx.AsyncClient() as client:
            response = await client.get(forecast_url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()

    cached = await get_or_load(
        f"open_meteo:forecast:{_coordinates_key(latitude, longitude)}",
        "Open-Meteo daily forecast",
        FORECAST_TTL,
        load,
    )
    return cached["data"]
def format_forecast(data: dict) -> list:
    daily = data["daily"]

    forecast = []

    for i in range(len(daily["time"])):
        weather_code = daily["weather_code"][i]

        forecast.append({
            "date": daily["time"][i],
            "condition": get_weather_condition(weather_code),
            "weather_code": weather_code,
            "temperature_max_c": daily["temperature_2m_max"][i],
            "temperature_min_c": daily["temperature_2m_min"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "wind_speed_max_kmh": daily["wind_speed_10m_max"][i],
        })

    return forecast
async def get_hourly_forecast(latitude: float, longitude: float):
    forecast_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        ],
        "forecast_days": 2,
        "timezone": "auto",
    }

    async def load():
        async with httpx.AsyncClient() as client:
            response = await client.get(forecast_url, params=params, timeout=10.0)
        response.raise_for_status()
        return response.json()

    cached = await get_or_load(
        f"open_meteo:hourly:{_coordinates_key(latitude, longitude)}",
        "Open-Meteo hourly forecast",
        HOURLY_TTL,
        load,
    )
    return cached["data"]
def format_hourly_forecast(data: dict) -> list:
    hourly = data["hourly"]

    forecast = []

    for i in range(len(hourly["time"])):
        weather_code = hourly["weather_code"][i]

        forecast.append({
            "time": hourly["time"][i],
            "temperature_c": hourly["temperature_2m"][i],
            "humidity_percent": hourly["relative_humidity_2m"][i],
            "rain_probability_percent": hourly["precipitation_probability"][i],
            "precipitation_mm": hourly["precipitation"][i],
            "condition": get_weather_condition(weather_code),
            "weather_code": weather_code,
            "wind_speed_kmh": hourly["wind_speed_10m"][i],
        })

    return forecast
