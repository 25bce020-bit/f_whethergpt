"""Verification script for Daily Outlook weather endpoints and multilingual responses."""

import asyncio
import sys
import httpx
import json

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"


async def test_daily_outlook():
    print("\n=================== 1. TESTING DAILY FORECAST DATA CONTRACT ===================")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        for city in ["Ahmedabad", "Mumbai", "Delhi"]:
            resp = await client.get(f"/gis/weather/forecast?name={city}")
            print(f"\nCity: {city} -> Status: {resp.status_code}")
            data = resp.json()
            forecast = data.get("forecast", [])
            print(f"Total Forecast Days: {len(forecast)}")
            if forecast:
                first = forecast[0]
                print(f"Day 0 Data:")
                print(f"  - Date: {first.get('date')}")
                print(f"  - Condition: {first.get('condition')}")
                print(f"  - Weather Code: {first.get('weather_code')}")
                print(f"  - Temp Max: {first.get('temperature_max_c')}°C")
                print(f"  - Temp Min: {first.get('temperature_min_c')}°C")
                print(f"  - Precipitation Sum: {first.get('precipitation_mm')} mm")
                print(f"  - Max Wind Speed: {first.get('wind_speed_max_kmh')} km/h")
                print(f"  - Humidity Field Present? {'humidity_percent' in first} (Honest backend omission: True)")

        print("\n=================== 2. TESTING CHAT DAILY OUTLOOK RESPONSES ===================")
        chat_queries = [
            ("English Multi-day", "What is the weather in Ahmedabad over the next few days?", "normal", "en"),
            ("Gujarati Unicode", "અમદાવાદમાં કાલે વરસાદ પડશે?", "normal", "gu"),
            ("Gujlish", "kale ahmedabad ma varsad padse?", "normal", "gu"),
            ("Hindi Unicode", "कल अहमदाबाद में बारिश होगी?", "normal", "hi"),
        ]

        for label, query, mode, expected_lang in chat_queries:
            print(f"\n--- Testing: {label} ---")
            print(f"Query: \"{query}\"")
            resp = await client.post("/chat", json={
                "message": query,
                "session_id": f"daily-test-{label.lower().replace(' ', '-')}",
                "selected_mode": mode,
            })
            if resp.status_code == 200:
                res_data = resp.json()
                print(f"Status: {resp.status_code}")
                print(f"Detected Language: {res_data.get('language')}, Script: {res_data.get('script')}")
                print(f"Active Mode: {res_data.get('active_mode')}")
                print(f"Has Forecast in Payload? {'forecast' in res_data and len(res_data.get('forecast', [])) > 0}")
                if 'forecast' in res_data and res_data['forecast']:
                    print(f"Forecast Days Count: {len(res_data['forecast'])}")
                print(f"Response: {res_data.get('response')[:200]}...")
            else:
                print(f"Failed with status {resp.status_code}: {resp.text}")


if __name__ == "__main__":
    asyncio.run(test_daily_outlook())
