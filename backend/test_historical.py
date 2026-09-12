import asyncio

from app.services.historical_service import (
    get_historical_weather,
    format_historical_weather
)


async def main():

    # Ahmedabad coordinates
    latitude = 23.0225
    longitude = 72.5714

    data = await get_historical_weather(
        latitude,
        longitude,
        "2026-08-29",
        "2026-08-29"
    )

    historical = format_historical_weather(data)

    print(historical)


asyncio.run(main())