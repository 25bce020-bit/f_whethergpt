"""Sprint 19 deterministic routing coverage; these tests never call Groq."""

import unittest

from app.services.mode_service import WeatherMode, resolve_mode
from app.services.query_service import understand_query


class NormalAutoRoutingTests(unittest.TestCase):
    def test_automatic_routes_keep_normal_selected_and_display_mode(self):
        cases = {
            "Should I irrigate my wheat tomorrow?": WeatherMode.FARMER,
            "Compare the GFS and Open-Meteo forecast for Ahmedabad tomorrow.": WeatherMode.RESEARCHER,
            "Is tomorrow a good day for travelling to Goa?": WeatherMode.TRAVELLER,
            "What is the weather in Ahmedabad tomorrow?": WeatherMode.NORMAL,
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                result = resolve_mode(message, WeatherMode.NORMAL)
                self.assertEqual(result.active_mode, expected)
                self.assertEqual(result.selected_mode, WeatherMode.NORMAL)
                self.assertEqual(result.display_mode, WeatherMode.NORMAL)

    def test_manual_modes_always_override_intent(self):
        cases = (
            (WeatherMode.FARMER, "Compare the GFS and Open-Meteo forecast for Ahmedabad."),
            (WeatherMode.RESEARCHER, "Should I carry a raincoat for my Goa trip?"),
            (WeatherMode.TRAVELLER, "Should I irrigate my wheat tomorrow?"),
            (WeatherMode.RESEARCHER, "Should I irrigate my wheat tomorrow?"),
            (WeatherMode.TRAVELLER, "Compare GFS and Open-Meteo."),
        )
        for selected, message in cases:
            with self.subTest(selected=selected):
                result = resolve_mode(message, selected)
                self.assertEqual(result.active_mode, selected)
                self.assertEqual(result.display_mode, selected)

    def test_false_positives_remain_normal_and_explicit_intent_routes(self):
        normal = (
            "What is the weather in Goa tomorrow?",
            "What is the weather in Ahmedabad?",
            "Will it rain tomorrow?",
            "What is the forecast for Mumbai?",
        )
        for message in normal:
            with self.subTest(message=message):
                self.assertEqual(resolve_mode(message, "normal").active_mode, WeatherMode.NORMAL)
        self.assertEqual(resolve_mode("Should I travel to Mumbai tomorrow?", "normal").active_mode, WeatherMode.TRAVELLER)
        self.assertEqual(resolve_mode("Compare GFS and Open-Meteo.", "normal").active_mode, WeatherMode.RESEARCHER)

    def test_agricultural_action_phrasing_routes_to_farmer(self):
        messages = (
            "Should I irrigate my wheat tomorrow?",
            "Should we irrigate our wheat tomorrow?",
            "Can I irrigate my wheat tomorrow?",
            "Should I sow my wheat tomorrow?",
            "Is tomorrow suitable for sowing wheat?",
            "Should I spray my cotton tomorrow?",
            "When should I harvest my crop?",
        )
        for message in messages:
            with self.subTest(message=message):
                self.assertEqual(resolve_mode(message, "normal").active_mode, WeatherMode.FARMER)

    def test_context_routes_only_relevant_follow_ups(self):
        trip_context = {"history": [{"user": "I'm planning a trip to Mumbai tomorrow."}]}
        crop_context = {"crop": "wheat", "history": [{"user": "I have wheat growing in Ahmedabad."}]}
        self.assertEqual(resolve_mode("Should I carry a raincoat?", "normal", trip_context).active_mode, WeatherMode.TRAVELLER)
        self.assertEqual(resolve_mode("Should I irrigate tomorrow?", "normal", crop_context).active_mode, WeatherMode.FARMER)
        self.assertEqual(resolve_mode("What is the temperature tomorrow?", "normal", crop_context).active_mode, WeatherMode.NORMAL)

    def test_normal_selection_does_not_stick_to_a_previous_automatic_mode(self):
        first = resolve_mode("Should I irrigate my wheat tomorrow?", "normal")
        second = resolve_mode("What is the temperature tomorrow?", first.selected_mode)
        self.assertEqual(first.active_mode, WeatherMode.FARMER)
        self.assertEqual(first.selected_mode, WeatherMode.NORMAL)
        self.assertEqual(second.active_mode, WeatherMode.NORMAL)
        self.assertEqual(second.selected_mode, WeatherMode.NORMAL)

    def test_location_extraction_regressions(self):
        self.assertEqual(understand_query("I am growing wheat in Ahmedabad. Is tomorrow suitable for sowing?")["location"], "ahmedabad")
        self.assertEqual(understand_query("Is tomorrow suitable for travelling to Goa?")["location"], "goa")
        self.assertEqual(understand_query("Compare GFS and Open-Meteo for Ahmedabad tomorrow.")["location"], "ahmedabad")


if __name__ == "__main__":
    unittest.main()
