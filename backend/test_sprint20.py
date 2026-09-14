"""Sprint 20 session-context and cross-mode regression coverage.

These tests exercise the deterministic context layer only; no weather provider or
LLM call is required.
"""

import unittest

from app.services.context_service import (
    MAX_HISTORY,
    clear_context,
    get_context,
    relevant_context,
    update_context,
)
from app.services.mode_service import WeatherMode, resolve_mode
from app.services.query_service import understand_query


class Sprint20ContextTests(unittest.TestCase):
    def setUp(self):
        self.session = "sprint20-primary"
        clear_context(self.session)

    def remember(self, message, query, *, location=None, **kwargs):
        update_context(self.session, message, "ok", query, location, **kwargs)

    def test_location_inheritance_and_existing_s19_sequence(self):
        self.remember("weather in Ahmedabad", {"intent": "current_weather", "time": "unspecified"}, location={"name": "Ahmedabad", "country": "India", "state": "Gujarat"})
        self.assertEqual(relevant_context(get_context(self.session), "normal")["location"], "Ahmedabad")
        self.remember("weather in Mumbai", {"intent": "current_weather", "time": "unspecified"}, location={"name": "Mumbai"})
        self.assertEqual(relevant_context(get_context(self.session), "normal")["location"], "Mumbai")

    def test_explicit_location_override_is_extractable(self):
        self.remember("weather in Ahmedabad", {"intent": "current_weather", "time": "unspecified"}, location={"name": "Ahmedabad"})
        self.assertEqual(understand_query("What is the weather in Mumbai?")["location"], "mumbai")

    def test_farmer_crop_growth_stage_and_location_context(self):
        self.remember("I am growing wheat in Ahmedabad", {"intent": "farmer_context", "time": "unspecified"}, location={"name": "Ahmedabad"}, crop="wheat", growth_stage="vegetative")
        context = relevant_context(get_context(self.session), "farmer")
        self.assertEqual((context["location"], context["crop"], context["growth_stage"]), ("Ahmedabad", "wheat", "vegetative"))
        self.assertEqual(resolve_mode("Should I irrigate tomorrow?", "normal", get_context(self.session)).active_mode, WeatherMode.FARMER)

    def test_farmer_memory_does_not_make_gfs_request_farmer(self):
        self.remember("I grow wheat", {"intent": "farmer_context", "time": "unspecified"}, crop="wheat")
        self.assertEqual(resolve_mode("What does GFS predict for tomorrow?", "normal", get_context(self.session)).active_mode, WeatherMode.RESEARCHER)

    def test_traveller_destination_and_time_context(self):
        self.remember("trip to Goa tomorrow", {"intent": "forecast", "time": "tomorrow", "location": "Goa"}, location={"name": "Goa"}, destination="Goa", travel_time="tomorrow")
        context = relevant_context(get_context(self.session), "traveller")
        self.assertEqual((context["destination"], context["travel_time"], context["location"]), ("Goa", "tomorrow", "Goa"))
        self.assertEqual(resolve_mode("Should I carry a raincoat?", "normal", get_context(self.session)).active_mode, WeatherMode.TRAVELLER)

    def test_traveller_destination_override(self):
        self.remember("trip to Goa tomorrow", {"intent": "forecast", "time": "tomorrow"}, destination="Goa", travel_time="tomorrow")
        self.remember("travelling to Mumbai instead", {"intent": "forecast", "time": "unspecified"}, location={"name": "Mumbai"}, destination="Mumbai")
        self.assertEqual(relevant_context(get_context(self.session), "traveller")["destination"], "Mumbai")
        self.assertEqual(understand_query("I'm travelling to Mumbai instead.")["location"], "mumbai")

    def test_researcher_context_continuation(self):
        self.remember("Compare GFS and Open-Meteo for Ahmedabad tomorrow", {"intent": "model_comparison", "time": "tomorrow"}, location={"name": "Ahmedabad"}, research_location="Ahmedabad", research_time="tomorrow", research_tool="model_comparison")
        context = get_context(self.session)
        filtered = relevant_context(context, "researcher")
        self.assertEqual(filtered["research_tool"], "model_comparison")
        self.assertEqual(resolve_mode("Which model agrees more?", "normal", context).active_mode, WeatherMode.RESEARCHER)

    def test_relevant_context_filters_other_mode_state(self):
        self.remember("all context", {"intent": "forecast", "time": "tomorrow"}, location={"name": "Ahmedabad"}, crop="wheat", growth_stage="vegetative", destination="Goa", travel_time="tomorrow", research_location="Pune", research_tool="nwp_gfs")
        normal = relevant_context(get_context(self.session), "normal")
        traveller = relevant_context(get_context(self.session), "traveller")
        researcher = relevant_context(get_context(self.session), "researcher")
        self.assertNotIn("crop", normal)
        self.assertNotIn("destination", normal)
        self.assertEqual(traveller["destination"], "Goa")
        self.assertNotIn("crop", traveller)
        self.assertEqual(researcher["research_location"], "Pune")
        self.assertNotIn("destination", researcher)

    def test_session_isolation(self):
        other = "sprint20-other"
        clear_context(other)
        self.remember("wheat in Ahmedabad", {"intent": "farmer_context", "time": "unspecified"}, location={"name": "Ahmedabad"}, crop="wheat")
        self.assertIsNone(get_context(other)["crop"])
        self.assertIsNone(relevant_context(get_context(other), "farmer")["location"])

    def test_manual_mode_precedence_and_automatic_mode_regressions(self):
        manual = resolve_mode("Should I irrigate wheat tomorrow?", "researcher", get_context(self.session))
        automatic = resolve_mode("Should I irrigate wheat tomorrow?", "normal", get_context(self.session))
        self.assertEqual(manual.active_mode, WeatherMode.RESEARCHER)
        self.assertEqual(automatic.active_mode, WeatherMode.FARMER)
        self.assertEqual(automatic.selected_mode, WeatherMode.NORMAL)

    def test_normal_mode_is_not_permanently_specialized(self):
        context = get_context(self.session)
        first = resolve_mode("Should I irrigate tomorrow?", "normal", {**context, "crop": "wheat"})
        second = resolve_mode("What is the temperature tomorrow?", first.selected_mode, context)
        self.assertEqual(first.active_mode, WeatherMode.FARMER)
        self.assertEqual(second.active_mode, WeatherMode.NORMAL)

    def test_history_is_bounded(self):
        for index in range(MAX_HISTORY + 3):
            self.remember(f"message {index}", {"intent": "current_weather", "time": "unspecified"})
        history = get_context(self.session)["history"]
        self.assertEqual(len(history), MAX_HISTORY)
        self.assertEqual(history[0]["user"], "message 3")


if __name__ == "__main__":
    unittest.main()
