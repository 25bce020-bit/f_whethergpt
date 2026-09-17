import unittest
from unittest.mock import AsyncMock, patch

from app import main as api
from app.services.context_service import clear_context
from app.services.mode_service import (
    WeatherMode,
    build_mode_mismatch_response,
    detect_automatic_mode,
    resolve_mode,
)


class ModeBoundariesUnitTests(unittest.TestCase):
    def test_detect_automatic_mode_signals(self):
        # Farming queries
        self.assertEqual(detect_automatic_mode("What fertilizer should I use for wheat?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("wheat crop mate kale varsad ni asar su thase?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("Will rain affect my wheat crop tomorrow?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("Should I irrigate my wheat field tomorrow?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("What weather is suitable for wheat farming?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("गेहूं की फसल के लिए कौन सा खाद इस्तेमाल करूं?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("ઘઉંના પાક માટે કયું ખાતર વાપરવું?"), WeatherMode.FARMER)
        self.assertEqual(detect_automatic_mode("wheat crop mate kayu khatar vapru?"), WeatherMode.FARMER)

        # Traveller queries
        self.assertEqual(detect_automatic_mode("Which hotel should I book in Mumbai?"), WeatherMode.TRAVELLER)
        self.assertEqual(detect_automatic_mode("Which hotel should I stay at in Mumbai?"), WeatherMode.TRAVELLER)
        self.assertEqual(detect_automatic_mode("Should I carry an umbrella on my trip?"), WeatherMode.TRAVELLER)
        self.assertEqual(detect_automatic_mode("Should I carry an umbrella during my vacation?"), WeatherMode.TRAVELLER)
        self.assertEqual(detect_automatic_mode("Will it rain during my trip to Mumbai?"), WeatherMode.TRAVELLER)
        self.assertEqual(detect_automatic_mode("What is the weather in Ahmedabad for my trip tomorrow?"), WeatherMode.TRAVELLER)

        # Researcher queries
        self.assertEqual(detect_automatic_mode("Compare GFS and other weather models."), WeatherMode.RESEARCHER)
        self.assertEqual(detect_automatic_mode("Compare GFS and other weather model forecasts."), WeatherMode.RESEARCHER)

        # General weather queries remain Normal
        self.assertEqual(detect_automatic_mode("What is the weather in Mumbai?"), WeatherMode.NORMAL)
        self.assertEqual(detect_automatic_mode("What is the weather in Ahmedabad?"), WeatherMode.NORMAL)
        self.assertEqual(detect_automatic_mode("What is the temperature in Delhi today?"), WeatherMode.NORMAL)

    def test_resolve_mode_normal_allows_auto_routing(self):
        res = resolve_mode("What weather is suitable for wheat farming?", WeatherMode.NORMAL)
        self.assertEqual(res.selected_mode, WeatherMode.NORMAL)
        self.assertEqual(res.active_mode, WeatherMode.FARMER)
        self.assertEqual(res.display_mode, WeatherMode.NORMAL)
        self.assertEqual(res.routing, "automatic")
        self.assertFalse(res.is_mismatch)
        self.assertIsNone(res.suggested_mode)

    def test_resolve_mode_specialized_scope_constraint(self):
        # 1. Traveller + fertilizer -> Mismatch (suggest Farmer)
        res1 = resolve_mode("What fertilizer should I use for wheat?", WeatherMode.TRAVELLER)
        self.assertTrue(res1.is_mismatch)
        self.assertEqual(res1.suggested_mode, WeatherMode.FARMER)
        self.assertEqual(res1.selected_mode, WeatherMode.TRAVELLER)

        # 2. Farmer + hotel -> Mismatch (suggest Traveller)
        res2 = resolve_mode("Which hotel should I stay at in Mumbai?", WeatherMode.FARMER)
        self.assertTrue(res2.is_mismatch)
        self.assertEqual(res2.suggested_mode, WeatherMode.TRAVELLER)
        self.assertEqual(res2.selected_mode, WeatherMode.FARMER)

        # 3. Researcher + umbrella on trip -> Mismatch (suggest Traveller)
        res3 = resolve_mode("Should I carry an umbrella on my trip?", WeatherMode.RESEARCHER)
        self.assertTrue(res3.is_mismatch)
        self.assertEqual(res3.suggested_mode, WeatherMode.TRAVELLER)
        self.assertEqual(res3.selected_mode, WeatherMode.RESEARCHER)

        # 4. Traveller + General weather -> Valid, NOT rejected
        res4 = resolve_mode("What is the weather in Mumbai?", WeatherMode.TRAVELLER)
        self.assertFalse(res4.is_mismatch)
        self.assertEqual(res4.selected_mode, WeatherMode.TRAVELLER)
        self.assertEqual(res4.active_mode, WeatherMode.TRAVELLER)

        # 5. Farmer + General weather -> Valid, NOT rejected
        res5 = resolve_mode("What is the weather in Ahmedabad tomorrow?", WeatherMode.FARMER)
        self.assertFalse(res5.is_mismatch)
        self.assertEqual(res5.selected_mode, WeatherMode.FARMER)
        self.assertEqual(res5.active_mode, WeatherMode.FARMER)

        # 6. Researcher + General weather -> Valid, NOT rejected
        res6 = resolve_mode("What is the weather in Delhi?", WeatherMode.RESEARCHER)
        self.assertFalse(res6.is_mismatch)
        self.assertEqual(res6.selected_mode, WeatherMode.RESEARCHER)
        self.assertEqual(res6.active_mode, WeatherMode.RESEARCHER)

    def test_build_mode_mismatch_response_multilingual(self):
        # English
        en_msg = build_mode_mismatch_response(WeatherMode.TRAVELLER, WeatherMode.FARMER, "en", "latin")
        self.assertIn("Farmer mode", en_msg)
        self.assertIn("agricultural", en_msg)

        # Gujlish
        gujlish_msg = build_mode_mismatch_response(WeatherMode.TRAVELLER, WeatherMode.FARMER, "gu", "latin")
        self.assertIn("Farmer mode", gujlish_msg)
        self.assertIn("Aa prashna", gujlish_msg)
        self.assertIn("switch karo", gujlish_msg)

        # Gujarati Unicode
        gu_msg = build_mode_mismatch_response(WeatherMode.TRAVELLER, WeatherMode.FARMER, "gu", "native")
        self.assertIn("Farmer મોડ", gu_msg)
        self.assertIn("આ પ્રશ્ન", gu_msg)

        # Hinglish
        hi_latin = build_mode_mismatch_response(WeatherMode.FARMER, WeatherMode.TRAVELLER, "hi", "latin")
        self.assertIn("Traveller mode", hi_latin)
        self.assertIn("Yeh sawal", hi_latin)

        # Hindi Unicode
        hi_native = build_mode_mismatch_response(WeatherMode.FARMER, WeatherMode.TRAVELLER, "hi", "native")
        self.assertIn("Traveller मोड", hi_native)
        self.assertIn("यह प्रश्न", hi_native)

        # Bengali
        bn_msg = build_mode_mismatch_response(WeatherMode.TRAVELLER, WeatherMode.FARMER, "bn", "native")
        self.assertIn("Farmer মোড", bn_msg)

        # Tamil
        ta_msg = build_mode_mismatch_response(WeatherMode.TRAVELLER, WeatherMode.FARMER, "ta", "native")
        self.assertIn("Farmer பயன்முறை", ta_msg)


class ModeBoundariesChatIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "test-mode-boundaries-session"
        clear_context(self.session_id)
        self.location = {"name": "Ahmedabad", "country": "India", "admin1": "Gujarat", "latitude": 23.02, "longitude": 72.57}
        self.current = {"current": {"time": "2026-09-14T09:00", "temperature_2m": 30, "relative_humidity_2m": 50, "apparent_temperature": 30, "precipitation": 0, "weather_code": 0, "wind_speed_10m": 10, "wind_direction_10m": 180}, "timezone": "Asia/Kolkata"}
        self.daily = {"daily": {"time": ["2026-09-14"], "weather_code": [0], "temperature_2m_max": [32], "temperature_2m_min": [24], "precipitation_sum": [0], "wind_speed_10m_max": [12]}}
        self.hourly = {"hourly": {"time": ["2026-09-14T08:00"], "temperature_2m": [30], "relative_humidity_2m": [50], "precipitation_probability": [0], "precipitation": [0], "weather_code": [0], "wind_speed_10m": [10]}}

    async def test_required_test_1_traveller_fertilizer(self):
        # TEST 1: Select Traveller -> Ask "What fertilizer should I use for wheat?" -> Suggest Farmer
        with patch.object(api, "save_chat_message", AsyncMock()):
            res = await api.chat(api.ChatRequest(
                message="What fertilizer should I use for wheat?",
                session_id=self.session_id,
                selected_mode=WeatherMode.TRAVELLER,
            ))
            self.assertTrue(res.get("mode_mismatch"))
            self.assertEqual(res.get("suggested_mode"), "farmer")
            self.assertEqual(res["selected_mode"], "traveller")
            self.assertIn("Farmer mode", res["response"])

    async def test_required_test_2_traveller_gujlish_wheat(self):
        # TEST 2: Select Traveller -> Ask "wheat crop mate kale varsad ni asar su thase?" -> Suggest Farmer in Roman Gujarati
        with patch.object(api, "save_chat_message", AsyncMock()):
            res = await api.chat(api.ChatRequest(
                message="wheat crop mate kale varsad ni asar su thase?",
                session_id=self.session_id,
                selected_mode=WeatherMode.TRAVELLER,
            ))
            self.assertTrue(res.get("mode_mismatch"))
            self.assertEqual(res.get("suggested_mode"), "farmer")
            self.assertEqual(res["selected_mode"], "traveller")
            self.assertEqual(res["language"], "gu")
            self.assertEqual(res["script"], "latin")
            self.assertIn("Farmer mode", res["response"])
            self.assertIn("Aa prashna", res["response"])

    async def test_required_test_3_farmer_wheat_rain(self):
        # TEST 3: Select Farmer -> Ask "Will it rain tomorrow for my wheat crop?" -> Farmer answer
        with patch.object(api, "save_chat_message", AsyncMock()), \
             patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Ahmedabad", "time": "tomorrow", "activity": None})), \
             patch.object(api, "search_location", AsyncMock(return_value=[self.location])), \
             patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)), \
             patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_hourly_forecast", AsyncMock(return_value=self.hourly)), \
             patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})), \
             patch.object(api, "generate_weather_response", AsyncMock(return_value="Farmer wheat advice")):
            res = await api.chat(api.ChatRequest(
                message="Will it rain tomorrow for my wheat crop?",
                session_id=self.session_id,
                selected_mode=WeatherMode.FARMER,
            ))
            self.assertFalse(res.get("mode_mismatch", False))
            self.assertEqual(res["selected_mode"], "farmer")
            self.assertEqual(res["active_mode"], "farmer")
            self.assertIn("farmer_advisory", res)

    async def test_required_test_4_farmer_hotel(self):
        # TEST 4: Select Farmer -> Ask "Which hotel should I book in Mumbai?" -> Suggest Traveller
        with patch.object(api, "save_chat_message", AsyncMock()):
            res = await api.chat(api.ChatRequest(
                message="Which hotel should I book in Mumbai?",
                session_id=self.session_id,
                selected_mode=WeatherMode.FARMER,
            ))
            self.assertTrue(res.get("mode_mismatch"))
            self.assertEqual(res.get("suggested_mode"), "traveller")
            self.assertEqual(res["selected_mode"], "farmer")
            self.assertIn("Traveller mode", res["response"])

    async def test_required_test_5_researcher_gfs(self):
        # TEST 5: Select Researcher -> Ask "Compare GFS and other weather models." -> Researcher answer
        with patch.object(api, "save_chat_message", AsyncMock()), \
             patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Ahmedabad", "time": "unspecified", "activity": None})), \
             patch.object(api, "search_location", AsyncMock(return_value=[self.location])), \
             patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)), \
             patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_gfs_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})), \
             patch.object(api, "generate_weather_response", AsyncMock(return_value="Researcher GFS analysis")):
            res = await api.chat(api.ChatRequest(
                message="Compare GFS and other weather models.",
                session_id=self.session_id,
                selected_mode=WeatherMode.RESEARCHER,
            ))
            self.assertFalse(res.get("mode_mismatch", False))
            self.assertEqual(res["selected_mode"], "researcher")
            self.assertEqual(res["active_mode"], "researcher")

    async def test_required_test_6_researcher_umbrella(self):
        # TEST 6: Select Researcher -> Ask "Should I carry an umbrella on my trip?" -> Suggest Traveller
        with patch.object(api, "save_chat_message", AsyncMock()):
            res = await api.chat(api.ChatRequest(
                message="Should I carry an umbrella on my trip?",
                session_id=self.session_id,
                selected_mode=WeatherMode.RESEARCHER,
            ))
            self.assertTrue(res.get("mode_mismatch"))
            self.assertEqual(res.get("suggested_mode"), "traveller")
            self.assertEqual(res["selected_mode"], "researcher")
            self.assertIn("Traveller mode", res["response"])

    async def test_required_test_7_normal_wheat_auto_routing(self):
        # TEST 7: Select Normal -> Ask "What weather is suitable for wheat farming?" -> Auto-routing to Farmer
        with patch.object(api, "save_chat_message", AsyncMock()), \
             patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Ahmedabad", "time": "unspecified", "activity": None})), \
             patch.object(api, "search_location", AsyncMock(return_value=[self.location])), \
             patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)), \
             patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_hourly_forecast", AsyncMock(return_value=self.hourly)), \
             patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})), \
             patch.object(api, "generate_weather_response", AsyncMock(return_value="Farmer wheat guidance")):
            res = await api.chat(api.ChatRequest(
                message="What weather is suitable for wheat farming?",
                session_id=self.session_id,
                selected_mode=WeatherMode.NORMAL,
            ))
            self.assertFalse(res.get("mode_mismatch", False))
            self.assertEqual(res["selected_mode"], "normal")
            self.assertEqual(res["active_mode"], "farmer")
            self.assertEqual(res["display_mode"], "normal")

    async def test_required_test_8_traveller_general_weather(self):
        # TEST 8: Select Traveller -> Ask "What is the weather in Ahmedabad?" -> Answer in Traveller context
        with patch.object(api, "save_chat_message", AsyncMock()), \
             patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "current_weather", "location": "Ahmedabad", "time": "unspecified", "activity": None})), \
             patch.object(api, "search_location", AsyncMock(return_value=[self.location])), \
             patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)), \
             patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_hourly_forecast", AsyncMock(return_value=self.hourly)), \
             patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})), \
             patch.object(api, "generate_weather_response", AsyncMock(return_value="Traveller Ahmedabad weather")):
            res = await api.chat(api.ChatRequest(
                message="What is the weather in Ahmedabad?",
                session_id=self.session_id,
                selected_mode=WeatherMode.TRAVELLER,
            ))
            self.assertFalse(res.get("mode_mismatch", False))
            self.assertEqual(res["selected_mode"], "traveller")
            self.assertEqual(res["active_mode"], "traveller")
            self.assertIn("traveller_advisory", res)

    async def test_required_test_9_traveller_trip_weather(self):
        # TEST 9: Select Traveller -> Ask "What is the weather in Ahmedabad for my trip tomorrow?" -> Answer in Traveller context
        with patch.object(api, "save_chat_message", AsyncMock()), \
             patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Ahmedabad", "time": "tomorrow", "activity": None})), \
             patch.object(api, "search_location", AsyncMock(return_value=[self.location])), \
             patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)), \
             patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_hourly_forecast", AsyncMock(return_value=self.hourly)), \
             patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})), \
             patch.object(api, "generate_weather_response", AsyncMock(return_value="Traveller Ahmedabad trip weather")):
            res = await api.chat(api.ChatRequest(
                message="What is the weather in Ahmedabad for my trip tomorrow?",
                session_id=self.session_id,
                selected_mode=WeatherMode.TRAVELLER,
            ))
            self.assertFalse(res.get("mode_mismatch", False))
            self.assertEqual(res["selected_mode"], "traveller")
            self.assertEqual(res["active_mode"], "traveller")

    async def test_required_test_10_switch_traveller_to_farmer(self):
        # TEST 10: Switch Traveller -> Farmer -> Ask "Will rain affect my wheat crop tomorrow?" -> Answer in Farmer context
        with patch.object(api, "save_chat_message", AsyncMock()), \
             patch.object(api, "understand_with_llm", AsyncMock(return_value={"intent": "forecast", "location": "Ahmedabad", "time": "tomorrow", "activity": None})), \
             patch.object(api, "search_location", AsyncMock(return_value=[self.location])), \
             patch.object(api, "get_current_weather", AsyncMock(return_value=self.current)), \
             patch.object(api, "get_forecast", AsyncMock(return_value=self.daily)), \
             patch.object(api, "get_hourly_forecast", AsyncMock(return_value=self.hourly)), \
             patch.object(api, "get_cached_imd_alerts", AsyncMock(return_value={"data": {"alerts": []}})), \
             patch.object(api, "generate_weather_response", AsyncMock(return_value="Farmer crop advice")):
            res = await api.chat(api.ChatRequest(
                message="Will rain affect my wheat crop tomorrow?",
                session_id=self.session_id,
                selected_mode=WeatherMode.FARMER,
            ))
            self.assertFalse(res.get("mode_mismatch", False))
            self.assertEqual(res["selected_mode"], "farmer")
            self.assertEqual(res["active_mode"], "farmer")
            self.assertIn("farmer_advisory", res)


if __name__ == "__main__":
    unittest.main()
