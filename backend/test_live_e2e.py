"""Live end-to-end testing script for WeatherGPT Map and Multilingual/Gujlish features."""

import asyncio
import sys
import httpx
import json

# Ensure console supports UTF-8 on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE_URL = "http://127.0.0.1:8000"


async def test_live_map_endpoints():
    print("\n=================== TESTING MAP ENDPOINTS ===================")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 1. Named location (Ahmedabad)
        print("\n--- 1. Named Location: Ahmedabad ---")
        current_res = await client.get("/gis/weather/current?name=Ahmedabad")
        print(f"Current weather status: {current_res.status_code}")
        current = current_res.json()
        print(f"Location: {current.get('location', {}).get('name')}, Temp: {current.get('weather', {}).get('temperature_c')}°C, Cond: {current.get('weather', {}).get('condition')}")

        forecast_res = await client.get("/gis/weather/forecast?name=Ahmedabad")
        print(f"Daily forecast status: {forecast_res.status_code}, Days: {len(forecast_res.json().get('forecast', []))}")

        hourly_res = await client.get("/gis/weather/hourly?name=Ahmedabad")
        print(f"Hourly forecast status: {hourly_res.status_code}, Hours: {len(hourly_res.json().get('hourly', []))}")

        warnings_res = await client.get("/weather/official-warnings?latitude=23.0225&longitude=72.5714")
        print(f"Warnings status: {warnings_res.status_code}, Alerts count: {warnings_res.json().get('location_alerts')}")

        advisory_res = await client.get("/weather/advisory-by-location?name=Ahmedabad")
        print(f"Advisory status: {advisory_res.status_code}, Advisories count: {len(advisory_res.json().get('advisories', []))}")

        # 2. Raw Coordinate selection
        print("\n--- 2. Raw Coordinates (23.0225, 72.5714) ---")
        coord_res = await client.get("/gis/weather/current?latitude=23.0225&longitude=72.5714")
        print(f"Coordinate weather status: {coord_res.status_code}")
        coord_data = coord_res.json()
        print(f"Point: ({coord_data.get('location', {}).get('latitude')}, {coord_data.get('location', {}).get('longitude')}), Temp: {coord_data.get('weather', {}).get('temperature_c')}°C")

        coord_hourly = await client.get("/gis/weather/hourly?latitude=23.0225&longitude=72.5714")
        print(f"Coordinate hourly status: {coord_hourly.status_code}, Hours: {len(coord_hourly.json().get('hourly', []))}")

        coord_forecast = await client.get("/gis/weather/forecast?latitude=23.0225&longitude=72.5714")
        print(f"Coordinate forecast status: {coord_forecast.status_code}, Days: {len(coord_forecast.json().get('forecast', []))}")


async def test_live_chat_languages():
    print("\n=================== TESTING MULTILINGUAL & GUJLISH CHAT ===================")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        test_queries = [
            ("English", "What is the current weather in Ahmedabad?", "normal", "session-en"),
            ("Hindi Unicode", "अहमदाबाद में आज मौसम कैसा है?", "normal", "session-hi"),
            ("Gujarati Unicode", "અમદાવાદમાં આજે હવામાન કેવું છે?", "normal", "session-gu"),
            ("Gujlish (1: Explicit City)", "ahmedabad ma kale bapore tapman su che", "normal", "session-gujlish-1"),
            ("Gujlish (2: Explicit City)", "aaje ahmedabad nu weather kevu che?", "normal", "session-gujlish-2"),
            ("Gujlish (3: Explicit City)", "ahmedabad ma kale varsad padse?", "normal", "session-gujlish-3"),
            ("Gujlish Farmer", "ahmedabad ma mari kheti mate kale nu havaman kevu rehse?", "farmer", "session-farmer-guj"),
            ("Hinglish", "ahmedabad me aaj mausam kaisa hai?", "normal", "session-hinglish"),
            ("Bengali", "আজ আহমেদাবাদের আবহাওয়া কেমন?", "normal", "session-bn"),
            ("Tamil", "அகமதாபாத்தில் இன்று வானிலை எப்படி உள்ளது?", "normal", "session-ta"),
            ("Marathi", "अहमदाबादमध्ये आज हवाમાન कसे आहे?", "normal", "session-mr"),
        ]

        for label, query, mode, session_id in test_queries:
            print(f"\n--- Testing: {label} ---")
            print(f"Input: \"{query}\" (Mode: {mode})")
            resp = await client.post("/chat", json={
                "message": query,
                "session_id": session_id,
                "selected_mode": mode,
            })
            if resp.status_code == 200:
                data = resp.json()
                print(f"Detected Lang: {data.get('language')}, Script: {data.get('script')}")
                print(f"Active Mode: {data.get('active_mode')}")
                print(f"Response: {data.get('response')[:250]}...")
            else:
                print(f"Failed with status {resp.status_code}: {resp.text}")

        # Contextual Follow-up with Gujlish in ONE session
        print("\n--- Testing: Contextual Follow-up in Gujlish ---")
        context_session = "session-context-gujlish"
        print("Turn 1: 'aaje ahmedabad nu weather kevu che?'")
        r1 = await client.post("/chat", json={
            "message": "aaje ahmedabad nu weather kevu che?",
            "session_id": context_session,
            "selected_mode": "normal",
        })
        print(f"Turn 1 Lang: {r1.json().get('language')}, Script: {r1.json().get('script')}")
        print(f"Turn 1 Response: {r1.json().get('response')[:150]}...")

        print("Turn 2: 'kale varsad padse?' (implicit location follow-up)")
        r2 = await client.post("/chat", json={
            "message": "kale varsad padse?",
            "session_id": context_session,
            "selected_mode": "normal",
        })
        print(f"Turn 2 Lang: {r2.json().get('language')}, Script: {r2.json().get('script')}")
        print(f"Turn 2 Response: {r2.json().get('response')[:200]}...")

        # Dynamic Language Switching Test in ONE session
        print("\n--- Testing: Dynamic Language Switching (4-step sequence in ONE session) ---")
        switching_session = "session-switching-test"
        sequence = [
            ("Step 1 (English)", "What is the weather in Delhi?"),
            ("Step 2 (Hindi)", "कल बारिश होगी?"),
            ("Step 3 (Gujlish)", "kale varsad padse?"),
            ("Step 4 (English)", "will it rain tomorrow?"),
        ]
        for step_label, msg in sequence:
            print(f"\n{step_label}: \"{msg}\"")
            resp = await client.post("/chat", json={
                "message": msg,
                "session_id": switching_session,
                "selected_mode": "normal",
            })
            if resp.status_code == 200:
                data = resp.json()
                print(f"Lang: {data.get('language')}, Script: {data.get('script')}")
                print(f"Response: {data.get('response')[:200]}...")
            else:
                print(f"Failed with status {resp.status_code}: {resp.text}")


async def main():
    await test_live_map_endpoints()
    await test_live_chat_languages()


if __name__ == "__main__":
    asyncio.run(main())
