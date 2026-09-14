import asyncio

from app.services.llm_service import choose_weather_tool


async def main():

    result = await choose_weather_tool(
        "Will it rain tomorrow in Mumbai?"
    )

    print("\nSELECTED TOOL:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
