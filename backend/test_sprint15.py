import unittest
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from app import main as api
from app.services.context_service import clear_context, get_context
from app.services.mode_service import (
    WeatherMode,
    detect_automatic_mode,
    resolve_mode,
    resolve_selected_mode,
)


class ModeServiceTests(unittest.TestCase):
    def test_default_and_ordinary_weather_are_normal(self):
        selected = resolve_selected_mode(None, was_explicitly_supplied=False)
        resolution = resolve_mode("What's the weather in Delhi tomorrow?", selected)
        self.assertEqual(resolution.selected_mode, WeatherMode.NORMAL)
        self.assertEqual(resolution.active_mode, WeatherMode.NORMAL)
        self.assertEqual(resolution.display_mode, WeatherMode.NORMAL)

    def test_manual_specialized_modes_override_automatic_detection(self):
        for mode in (WeatherMode.FARMER, WeatherMode.RESEARCHER, WeatherMode.TRAVELLER):
            with self.subTest(mode=mode):
                resolution = resolve_mode("Compare GFS and WRF precipitation forecasts.", mode)
                self.assertEqual(resolution.active_mode, mode)
                self.assertEqual(resolution.display_mode, mode)
                self.assertEqual(resolution.routing, "manual")

    def test_automatic_specialized_modes_keep_normal_display_mode(self):
        cases = {
            "Should I irrigate my wheat crop tomorrow?": WeatherMode.FARMER,
            "Compare GFS and WRF rainfall predictions.": WeatherMode.RESEARCHER,
            "I'm travelling to Goa this weekend. Will rain affect my trip?": WeatherMode.TRAVELLER,
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                resolution = resolve_mode(message, WeatherMode.NORMAL)
                self.assertEqual(resolution.selected_mode, WeatherMode.NORMAL)
                self.assertEqual(resolution.active_mode, expected)
                self.assertEqual(resolution.display_mode, WeatherMode.NORMAL)

    def test_detection_is_conservative(self):
        self.assertEqual(detect_automatic_mode("Will it rain in Delhi tomorrow?"), WeatherMode.NORMAL)

    def test_invalid_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            resolve_mode("Weather in Delhi", "invalid_value")
        with self.assertRaises(ValidationError):
            api.ChatRequest(message="Weather in Delhi", selected_mode="invalid_value")


class ChatModeIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "sprint15-mode-session"
        clear_context(self.session_id)

    async def _chat_greeting(self, **kwargs):
        with patch.object(api, "save_chat_message", AsyncMock()):
            return await api.chat(api.ChatRequest(message="Hi", session_id=self.session_id, **kwargs))

    async def test_default_contract_and_session_persistence(self):
        farmer = await self._chat_greeting(selected_mode="farmer")
        self.assertEqual(farmer["selected_mode"], "farmer")
        self.assertEqual(farmer["active_mode"], "farmer")
        self.assertEqual(farmer["display_mode"], "farmer")
        self.assertEqual(get_context(self.session_id)["selected_mode"], "farmer")

        retained = await self._chat_greeting()
        self.assertEqual(retained["selected_mode"], "farmer")
        self.assertEqual(retained["active_mode"], "farmer")

        normal = await self._chat_greeting(selected_mode="normal")
        self.assertEqual(normal["selected_mode"], "normal")
        self.assertEqual(get_context(self.session_id)["selected_mode"], "normal")

    async def test_mode_switching_in_one_session(self):
        for mode in ("normal", "farmer", "researcher", "traveller"):
            response = await self._chat_greeting(selected_mode=mode)
            self.assertEqual(response["selected_mode"], mode)
            self.assertEqual(response["active_mode"], mode)
            self.assertEqual(response["display_mode"], mode)

    async def test_greeting_contract_remains_intact(self):
        response = await self._chat_greeting()
        self.assertEqual(response["tool"]["tool"], "conversation")
        self.assertTrue(response["response"])
        self.assertEqual(response["selected_mode"], "normal")


if __name__ == "__main__":
    unittest.main()
