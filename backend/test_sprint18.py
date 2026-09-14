import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app import main as api
from app.services.context_service import clear_context
from app.services.mode_service import WeatherMode, get_mode_configuration, resolve_mode
from app.services.query_service import understand_query
from app.services.traveller_service import build_traveller_advisory, format_traveller_advisory
from app.services import location_service


DRY_DAY = {"date": "2026-09-14", "condition": "Clear sky", "weather_code": 0, "precipitation_mm": 0, "wind_speed_max_kmh": 10, "temperature_max_c": 30}
CURRENT = {"time": "2026-09-14T09:00", "temperature_c": 27, "precipitation_mm": 0, "wind_speed_kmh": 8, "condition": "Clear sky"}


class TravellerServiceTests(unittest.TestCase):
    def advisory(self, day=DRY_DAY, hours=None, warnings=None):
        return build_traveller_advisory(destination="Goa", current_weather=CURRENT, forecast=[day] if day else [], hourly_forecast=hours or [], imd_warnings=warnings or [], time_hint="today")

    def test_mode_configuration_and_manual_routing(self):
        self.assertIn("travel", get_mode_configuration(WeatherMode.TRAVELLER).persona_prompt.lower())
        resolved = resolve_mode("weather in Goa", WeatherMode.TRAVELLER)
        self.assertEqual((resolved.selected_mode, resolved.active_mode, resolved.display_mode), (WeatherMode.TRAVELLER,) * 3)

    def test_suitability_rules_cover_dry_rain_wind_and_thunderstorm(self):
        self.assertEqual(self.advisory()["travel_suitability"]["status"], "GOOD")
        self.assertEqual(self.advisory(hours=[{"rain_probability_percent": 80, "precipitation_mm": 0, "wind_speed_kmh": 8, "weather_code": 0}])["travel_suitability"]["status"], "CAUTION")
        self.assertEqual(self.advisory(day={**DRY_DAY, "precipitation_mm": 30})["travel_suitability"]["status"], "UNFAVORABLE")
        self.assertEqual(self.advisory(hours=[{"rain_probability_percent": 0, "precipitation_mm": 0, "wind_speed_kmh": 40, "weather_code": 0}])["travel_suitability"]["status"], "CAUTION")
        self.assertEqual(self.advisory(hours=[{"rain_probability_percent": 0, "precipitation_mm": 0, "wind_speed_kmh": 8, "weather_code": 95}])["travel_suitability"]["status"], "UNFAVORABLE")

    def test_warning_and_no_data_are_explicit_and_distinguishable(self):
        warning = self.advisory(warnings=[{"event": "Thunderstorm warning", "severity": "Severe"}])
        self.assertEqual(warning["travel_suitability"]["status"], "UNFAVORABLE")
        self.assertIn("official_imd_warning", warning["imd_actions"][0])
        self.assertIn("weathergpt_traveller_advice", warning["imd_actions"][0])
        unavailable = build_traveller_advisory(destination="Goa", current_weather=None, forecast=[], hourly_forecast=[], imd_warnings=None)
        self.assertEqual(unavailable["travel_suitability"]["status"], "UNAVAILABLE")
        self.assertIsNone(unavailable["best_window"])
        self.assertIn("hourly forecast data were not supplied", format_traveller_advisory(unavailable))

    def test_packing_outdoor_and_best_hourly_window_are_weather_grounded(self):
        hours = [
            {"time": "2026-09-14T08:00", "rain_probability_percent": 0, "precipitation_mm": 0, "wind_speed_kmh": 8, "weather_code": 0},
            {"time": "2026-09-14T14:00", "rain_probability_percent": 90, "precipitation_mm": 1, "wind_speed_kmh": 8, "weather_code": 61},
        ]
        advisory = self.advisory(day={**DRY_DAY, "temperature_max_c": 34}, hours=hours)
        self.assertEqual(advisory["best_window"]["period"], "morning")
        self.assertEqual(advisory["outdoor_activity"]["status"], "CAUTION")
        self.assertIn("Carry water.", advisory["packing"])
        self.assertIn("umbrella", " ".join(advisory["packing"]).lower())

    def test_location_and_time_extraction_stay_separate(self):
        goa = understand_query("Is tomorrow suitable for travelling to Goa?")
        mumbai = understand_query("What should I pack for Mumbai tomorrow?")
        delhi = understand_query("Is the weather suitable for travelling to Delhi day after tomorrow?")
        self.assertEqual((goa["location"], goa["time"]), ("goa", "tomorrow"))
        self.assertEqual((mumbai["location"], mumbai["time"]), ("mumbai", "tomorrow"))
        self.assertEqual((delhi["location"], delhi["time"]), ("delhi", "day_after_tomorrow"))

    def test_goa_uses_indian_alias_when_geocoder_has_no_indian_candidate(self):
        provider_results = {"results": [{"name": "Genoa", "country": "Italy", "country_code": "IT", "latitude": 44.4, "longitude": 8.9}]}
        with patch.object(location_service, "get_or_load", AsyncMock(return_value={"data": provider_results})):
            result = asyncio.run(location_service.search_location("Goa"))
        self.assertEqual((result[0]["name"], result[0]["country_code"]), ("Goa", "IN"))


class TravellerChatIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "sprint18-traveller"
        clear_context(self.session_id)
        self.location = {"name": "Goa", "country": "India", "admin1": "Goa", "latitude": 15.3, "longitude": 74.1}
        self.current = {"current": {"time": "2026-09-14T09:00", "temperature_2m": 27, "relative_humidity_2m": 65, "apparent_temperature": 27, "precipitation": 0, "weather_code": 0, "wind_speed_10m": 8, "wind_direction_10m": 90}, "timezone": "Asia/Kolkata"}
        self.daily = {"daily": {"time": ["2026-09-14"], "weather_code": [0], "temperature_2m_max": [30], "temperature_2m_min": [22], "precipitation_sum": [0], "wind_speed_10m_max": [10]}}
        self.hourly = {"hourly": {"time": ["2026-09-14T08:00"], "temperature_2m": [27], "relative_humidity_2m": [65], "precipitation_probability": [0], "precipitation": [0], "weather_code": [0], "wind_speed_10m": [8]}}

    async def test_manual_traveller_uses_structured_advisory_and_session_location(self):
        response_mock = AsyncMock(return_value="Traveller response")
        common = (
            patch.object(api, "save_chat_message", AsyncMock()),
            patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Goa", "time": "today", "activity": None})),
            patch.object(api, "choose_weather_tool", AsyncMock(return_value={"tool": "forecast", "reason": "forecast"})),
            patch.object(api, "search_location", AsyncMock(return_value=[self.location])),
            patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)),
            patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)),
            patch.object(api, "get_hourly_forecast", AsyncMock(return_value=self.hourly)),
            patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})),
            patch.object(api, "generate_weather_response", response_mock),
        )
        with common[0], common[1], common[2], common[3], common[4], common[5], common[6], common[7], common[8]:
            response = await api.chat(api.ChatRequest(message="How is the weather in Goa tomorrow?", session_id=self.session_id, selected_mode="traveller"))
        self.assertEqual((response["selected_mode"], response["active_mode"], response["display_mode"]), ("traveller",) * 3)
        self.assertIn("traveller_advisory", response)
        self.assertIn("traveller_advisory", response_mock.await_args.args[1])


if __name__ == "__main__":
    unittest.main()
