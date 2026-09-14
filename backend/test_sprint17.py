import unittest
from unittest.mock import AsyncMock, patch

from app import main as api
from app.services.context_service import clear_context, get_context
from app.services.mode_service import WeatherMode, get_mode_configuration, resolve_mode
from app.services.query_service import understand_query
from app.services.researcher_service import (
    build_researcher_analysis,
    choose_researcher_tool,
    format_researcher_analysis,
)


HISTORICAL = [
    {"date": "2026-09-10", "temperature_max_c": 30, "temperature_min_c": 20, "precipitation_mm": 1, "wind_speed_max_kmh": 10},
    {"date": "2026-09-11", "temperature_max_c": 32, "temperature_min_c": 22, "precipitation_mm": 5, "wind_speed_max_kmh": 12},
]


class ResearcherModeTests(unittest.TestCase):
    def test_researcher_configuration_exists(self):
        configuration = get_mode_configuration(WeatherMode.RESEARCHER)
        self.assertEqual(configuration.name, "Researcher Mode")
        self.assertIn("retrieved", configuration.persona_prompt)

    def test_manual_and_automatic_researcher_routing(self):
        manual = resolve_mode("What should I do with wheat tomorrow?", WeatherMode.RESEARCHER)
        self.assertEqual((manual.selected_mode, manual.active_mode, manual.display_mode), (WeatherMode.RESEARCHER,) * 3)

        automatic = resolve_mode("Analyze the rainfall trend in Ahmedabad.", WeatherMode.NORMAL)
        self.assertEqual(automatic.selected_mode, WeatherMode.NORMAL)
        self.assertEqual(automatic.active_mode, WeatherMode.RESEARCHER)
        self.assertEqual(automatic.display_mode, WeatherMode.NORMAL)

    def test_normal_and_farmer_routing_are_not_regressed(self):
        self.assertEqual(resolve_mode("What is the weather in Ahmedabad tomorrow?", WeatherMode.NORMAL).active_mode, WeatherMode.NORMAL)
        self.assertEqual(resolve_mode("Should I irrigate my wheat crop tomorrow?", WeatherMode.NORMAL).active_mode, WeatherMode.FARMER)

    def test_researcher_tool_fallback_handles_explicit_research_requests(self):
        self.assertEqual(choose_researcher_tool("Compare GFS and Open-Meteo"), "model_comparison")
        self.assertEqual(choose_researcher_tool("Analyze recent weather history"), "historical_weather")
        self.assertEqual(choose_researcher_tool("Analyze rainfall trend"), "climate")

    def test_researcher_location_fallback_handles_common_analysis_wording(self):
        self.assertEqual(understand_query("Analyze the recent weather history of Ahmedabad.")["location"], "ahmedabad")
        self.assertEqual(understand_query("Analyze Ahmedabad weather tomorrow.")["location"], "ahmedabad")


class ResearcherServiceTests(unittest.TestCase):
    def test_historical_analysis_is_structured_and_limited_to_retrieved_period(self):
        analysis = build_researcher_analysis({"location": {"name": "Ahmedabad"}, "historical_weather": HISTORICAL}, "historical_weather")
        summary = analysis["observations"]["historical_summary"]
        self.assertEqual(summary["total_precipitation_mm"], 6.0)
        self.assertEqual(summary["observed_temperature_direction"], "increasing")
        self.assertIn("long-term climate trend", analysis["limitations"][0])
        self.assertIn("Research Summary", format_researcher_analysis(analysis))

    def test_model_comparison_uses_existing_values_without_new_confidence(self):
        comparison = [{"date": "2026-09-14", "confidence": "moderate", "temperature": {"difference_c": 2}}]
        analysis = build_researcher_analysis({"location": {"name": "Ahmedabad"}, "comparison": comparison}, "model_comparison")
        self.assertEqual(analysis["observations"]["model_comparison"], comparison)
        self.assertEqual(analysis["observations"]["comparison_confidence"], ["moderate"])
        self.assertIn("not certainty", analysis["interpretation"][0])

    def test_imd_warning_is_separate_from_derived_analysis(self):
        analysis = build_researcher_analysis({
            "warnings": [{"event": "Heavy rainfall warning", "severity": "Severe"}],
            "alerts": [{"type": "heavy_rain"}],
        }, "official_warning")
        self.assertIn("IMD official warning", analysis["sources"])
        self.assertIn("official_imd_warnings", analysis["observations"])
        self.assertIn("weathergpt_derived_risks", analysis["observations"])
        self.assertTrue(any("official IMD" in item for item in analysis["interpretation"]))


class ResearcherChatIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "sprint17-researcher"
        clear_context(self.session_id)
        self.location = {"name": "Ahmedabad", "country": "India", "admin1": "Gujarat", "latitude": 23.0, "longitude": 72.0}
        self.raw_daily = {"daily": {"time": ["2026-09-14"], "weather_code": [0], "temperature_2m_max": [30], "temperature_2m_min": [20], "precipitation_sum": [0], "wind_speed_10m_max": [10]}}

    async def test_manual_researcher_uses_persona_and_structured_analysis(self):
        response_mock = AsyncMock(return_value="Research response")
        with (
            patch.object(api, "save_chat_message", AsyncMock()),
            patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Ahmedabad", "time": "tomorrow", "activity": None})),
            patch.object(api, "choose_weather_tool", AsyncMock(return_value={"tool": "forecast", "reason": "forecast"})),
            patch.object(api, "search_location", AsyncMock(return_value=[self.location])),
            patch.object(api, "get_forecast", AsyncMock(return_value=self.raw_daily)),
            patch.object(api, "generate_weather_response", response_mock),
        ):
            response = await api.chat(api.ChatRequest(message="Analyze the weather in Ahmedabad tomorrow.", session_id=self.session_id, selected_mode="researcher"))
        self.assertEqual((response["selected_mode"], response["active_mode"], response["display_mode"]), ("researcher",) * 3)
        payload = response_mock.await_args.args[1]
        self.assertIn("researcher_analysis", payload)
        self.assertIn("retrieved", response_mock.await_args.kwargs["mode_persona"])

    async def test_researcher_follow_up_reuses_location(self):
        context = get_context(self.session_id)
        context["location"] = "Ahmedabad"
        with (
            patch.object(api, "save_chat_message", AsyncMock()),
            patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "nwp_gfs", "location": None, "time": "unspecified", "activity": None})),
            patch.object(api, "choose_weather_tool", AsyncMock(return_value={"tool": "nwp_gfs", "reason": "GFS"})),
            patch.object(api, "search_location", AsyncMock(return_value=[self.location])) as search,
            patch.object(api, "get_cached_location_data", AsyncMock(return_value=None)),
            patch.object(api, "get_gfs_forecast", AsyncMock(return_value={"hourly": {}, "daily": {}})),
            patch.object(api, "format_gfs_forecast", return_value={"model": "NCEP GFS", "provider": "NOAA", "daily": [], "hourly": []}),
            patch.object(api, "generate_weather_response", AsyncMock(return_value="GFS response")),
        ):
            response = await api.chat(api.ChatRequest(message="What does the GFS model say?", session_id=self.session_id, selected_mode="researcher"))
        search.assert_awaited_once_with("Ahmedabad")
        self.assertEqual(response["location"]["name"], "Ahmedabad")


if __name__ == "__main__":
    unittest.main()
