from app.services.mode_engines.traveller_engine import TravellerEngine
from app.services.traveller_service import build_traveller_advisory


def test_traveller_engine_builds_structured_advisory():
    engine = TravellerEngine()
    result = __import__("asyncio").run(
        engine.process(
            request_message="Is it good to travel tomorrow?",
            query={"time": "tomorrow"},
            base_context={
                "location": {"name": "Ahmedabad"},
                "current_weather": {"temperature_c": 30},
                "forecast": [
                    {
                        "date": "2099-01-01",
                        "temperature_max_c": 31,
                        "temperature_min_c": 22,
                        "precipitation_mm": 2,
                        "wind_speed_max_kmh": 18,
                        "weather_code": 2,
                        "condition": "Partly cloudy",
                    }
                ],
                "hourly_forecast": [],
                "imd_warnings": [],
            },
        )
    )
    assert result["mode"] == "traveller"
    assert "traveller_advisory" in result
    assert result["traveller_advisory"]["destination"] == "Ahmedabad"


def test_traveller_advisory_distinguishes_official_warning_from_heuristic():
    advisory = build_traveller_advisory(
        destination="Mumbai",
        current_weather={"temperature_c": 29},
        forecast=[
            {
                "date": "2099-01-01",
                "temperature_max_c": 30,
                "temperature_min_c": 24,
                "precipitation_mm": 5,
                "wind_speed_max_kmh": 20,
                "weather_code": 61,
                "condition": "Rain",
            }
        ],
        hourly_forecast=[],
        imd_warnings=[
            {
                "event": "Heavy Rain",
                "severity": "Yellow",
                "headline": "Heavy rain warning",
                "description": "Heavy rain expected.",
            }
        ],
        time_hint="tomorrow",
    )
    assert advisory["imd_warning_status"] == "available"
    assert advisory["imd_actions"][0]["official_imd_warning"]["event"] == "Heavy Rain"
    assert "weathergpt_traveller_advice" in advisory["imd_actions"][0]


def test_traveller_engine_does_not_fetch_data():
    engine = TravellerEngine()
    result = __import__("asyncio").run(
        engine.process(
            request_message="What should I pack?",
            query={"time": "unspecified"},
            base_context={
                "location": {"name": "Pune"},
                "current_weather": None,
                "forecast": [],
                "hourly_forecast": [],
                "imd_warnings": None,
            },
        )
    )
    assert result["traveller_advisory"]["hourly_data_status"] == "unavailable"
    assert result["traveller_advisory"]["imd_warning_status"] == "unavailable"
