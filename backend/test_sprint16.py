import unittest
from unittest.mock import AsyncMock, patch

from app import main as api
from app.services.context_service import clear_context, get_context
from app.services.farmer_service import (
    build_farmer_advisory,
    extract_farmer_context,
    format_farmer_advisory,
)


DRY_DAY = {"date": "2026-09-14", "condition": "Clear sky", "weather_code": 0, "precipitation_mm": 0, "wind_speed_max_kmh": 10, "temperature_max_c": 30, "temperature_min_c": 20}
RAINY_DAY = {"date": "2026-09-14", "condition": "Heavy rain", "weather_code": 65, "precipitation_mm": 30, "wind_speed_max_kmh": 12, "temperature_max_c": 28, "temperature_min_c": 21}
CURRENT = {"time": "2026-09-13T09:00", "temperature_c": 27, "precipitation_mm": 0, "wind_speed_kmh": 8, "condition": "Clear sky"}


class FarmerServiceTests(unittest.TestCase):
    def advisory(self, *, day=DRY_DAY, hours=None, warnings=None):
        return build_farmer_advisory(
            crop="wheat", growth_stage="flowering", current_weather=CURRENT,
            forecast=[day], hourly_forecast=hours or [], imd_warnings=warnings or [], time_hint="today",
        )

    def test_crop_and_growth_stage_extraction_supports_multiple_crops(self):
        self.assertEqual(extract_farmer_context("I grow wheat") ["crop"], "wheat")
        self.assertEqual(extract_farmer_context("My paddy is flowering") ["crop"], "rice")
        self.assertEqual(extract_farmer_context("Tomato crop in fruiting stage") ["growth_stage"], "fruiting/grain filling")
        self.assertEqual(extract_farmer_context("What should I do today?") ["crop"], None)

    def test_irrigation_and_harvest_are_cautious_when_rain_is_forecast(self):
        advisory = self.advisory(day=RAINY_DAY)
        self.assertIn("may be unnecessary", advisory["irrigation"]["recommendation"])
        self.assertIn("Avoid harvesting", advisory["harvesting"]["recommendation"])
        self.assertIn("soil-moisture", advisory["irrigation"]["reason"])

    def test_dry_weather_and_calm_window_support_spraying_and_sowing(self):
        advisory = self.advisory()
        self.assertIn("more suitable for spraying", advisory["spraying"]["recommendation"])
        self.assertIn("generally suitable for sowing", advisory["sowing"]["recommendation"])
        self.assertIn("maturity cannot", advisory["harvesting"]["recommendation"])

    def test_wind_and_thunderstorm_block_spraying(self):
        advisory = self.advisory(hours=[{"rain_probability_percent": 0, "precipitation_mm": 0, "wind_speed_kmh": 30, "weather_code": 95}])
        self.assertIn("Delay spraying", advisory["spraying"]["recommendation"])
        self.assertTrue(any("Avoid exposed" in item for item in advisory["today_advisory"]))

    def test_insufficient_weather_data_is_explicit(self):
        advisory = build_farmer_advisory(crop=None, growth_stage=None, current_weather=None, forecast=[], hourly_forecast=[], imd_warnings=[])
        self.assertEqual(advisory["irrigation"]["confidence"], "low")
        self.assertIn("cannot be assessed", advisory["spraying"]["recommendation"])

    def test_imd_actions_distinguish_official_warning_and_derived_advice(self):
        advisory = self.advisory(warnings=[{"event": "Heavy rainfall warning", "severity": "Severe", "headline": "Heavy rain"}])
        action = advisory["imd_actions"][0]
        self.assertEqual(action["official_imd_warning"]["event"], "Heavy rainfall warning")
        self.assertIn("drainage", action["weathergpt_farmer_advisory"])
        rendered = format_farmer_advisory(advisory)
        self.assertIn("Official IMD warning", rendered)
        self.assertIn("WeatherGPT farmer advisory", rendered)


class FarmerChatIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "sprint16-farmer"
        clear_context(self.session_id)

    async def test_crop_and_stage_persist_in_session_context(self):
        with patch.object(api, "save_chat_message", AsyncMock()):
            first = await api.chat(api.ChatRequest(message="I grow wheat", session_id=self.session_id, selected_mode="farmer"))
            second = await api.chat(api.ChatRequest(message="It is flowering", session_id=self.session_id))
        self.assertEqual(first["farmer_context"]["crop"], "wheat")
        self.assertEqual(second["farmer_context"]["growth_stage"], "flowering")
        self.assertEqual(get_context(self.session_id)["crop"], "wheat")
        self.assertEqual(get_context(self.session_id)["growth_stage"], "flowering")

    async def test_normal_mode_auto_farmer_keeps_selected_mode_and_returns_advisory(self):
        location = {"name": "Ahmedabad", "country": "India", "admin1": "Gujarat", "latitude": 23.0, "longitude": 72.0}
        raw_current = {"current": {"time": "2026-09-13T09:00", "temperature_2m": 27, "relative_humidity_2m": 60, "apparent_temperature": 27, "precipitation": 0, "weather_code": 0, "wind_speed_10m": 8, "wind_direction_10m": 90}, "timezone": "Asia/Kolkata"}
        raw_daily = {"daily": {"time": ["2026-09-13"], "weather_code": [0], "temperature_2m_max": [30], "temperature_2m_min": [20], "precipitation_sum": [0], "wind_speed_10m_max": [10]}}
        raw_hourly = {"hourly": {"time": ["2026-09-13T10:00"], "temperature_2m": [28], "relative_humidity_2m": [55], "precipitation_probability": [0], "precipitation": [0], "weather_code": [0], "wind_speed_10m": [9]}}
        with (
            patch.object(api, "save_chat_message", AsyncMock()),
            patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "recommendation", "location": "Ahmedabad", "time": "today", "activity": None})),
            patch.object(api, "choose_weather_tool", AsyncMock(return_value={"tool": "recommendation", "reason": "farm advice"})),
            patch.object(api, "search_location", AsyncMock(return_value=[location])),
            patch.object(api, "get_current_weather", AsyncMock(return_value=raw_current)),
            patch.object(api, "get_forecast", AsyncMock(return_value=raw_daily)),
            patch.object(api, "get_hourly_forecast", AsyncMock(return_value=raw_hourly)),
            patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})),
            patch.object(api, "generate_weather_response", AsyncMock(return_value="Weather-grounded farmer response")),
        ):
            response = await api.chat(api.ChatRequest(message="Should I irrigate my wheat crop today in Ahmedabad?", session_id=self.session_id, selected_mode="normal"))
        self.assertEqual(response["selected_mode"], "normal")
        self.assertEqual(response["active_mode"], "farmer")
        self.assertEqual(response["tool"]["tool"], "farmer_advisory")
        self.assertEqual(response["farmer_advisory"]["crop"], "wheat")


if __name__ == "__main__":
    unittest.main()
