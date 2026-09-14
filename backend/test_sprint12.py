import unittest
from unittest.mock import AsyncMock, patch

from app import main as api
from app.services import llm_service
from app.services.context_service import clear_context, get_context, update_context
from app.services.language_service import (
    SUPPORTED_LANGUAGES,
    canonicalize_for_fallback,
    detect_language,
    extract_location_hint,
    get_language_instruction,
    normalize_language,
    resolve_response_language,
)
from app.services.location_service import normalize_location_name
from app.services.query_service import understand_query


class LanguageServiceTests(unittest.TestCase):
    def test_supported_registry_and_normalization(self):
        self.assertEqual(set(SUPPORTED_LANGUAGES), {"en", "hi", "gu", "mr", "bn", "ta", "te", "kn", "ml", "pa", "or"})
        self.assertEqual(normalize_language("Hindi"), "hi")
        self.assertEqual(normalize_language("gu-IN"), "gu")
        self.assertIsNone(normalize_language("fr"))

    def test_script_detection(self):
        self.assertEqual(detect_language("अहमदाबाद में कल बारिश होगी?"), "hi")
        self.assertEqual(detect_language("અમદાવાદમાં કાલે વરસાદ પડશે?"), "gu")
        self.assertEqual(detect_language("சென்னையில் நாளை மழை பெய்யுமா?"), "ta")

    def test_selection_and_english_fallback(self):
        self.assertEqual(resolve_response_language("hi", "hello", "gu"), "hi")
        self.assertEqual(resolve_response_language(None, "અમદાવાદમાં વરસાદ?", "hi"), "gu")
        self.assertEqual(resolve_response_language(None, "weather tomorrow", None), "en")

    def test_hinglish_fallback_and_location_regression(self):
        normalized = canonicalize_for_fallback("Ahmedabad mein kal baarish hogi?", "hi")
        query = understand_query(normalized)
        self.assertEqual(query["intent"], "forecast")
        self.assertEqual(query["time"], "tomorrow")
        self.assertEqual(extract_location_hint("Ahmedabad mein kal baarish hogi?", "hi"), "Ahmedabad")
        self.assertEqual(normalize_location_name("Ahmedabad mein"), "Ahmedabad")
        self.assertEqual(normalize_location_name("Ahmedabad. is"), "Ahmedabad")

    def test_context_persists_language_and_location(self):
        session = "sprint12-context"
        clear_context(session)
        update_context(session, "Ahmedabad mein kal weather", "उत्तर", {"intent": "forecast", "time": "tomorrow", "language": "hi"}, {"name": "Ahmedabad"})
        context = get_context(session)
        self.assertEqual(context["language"], "hi")
        self.assertEqual(context["location"], "Ahmedabad")


class LlmLanguagePromptTests(unittest.IsolatedAsyncioTestCase):
    async def test_response_prompt_has_target_language(self):
        with patch.object(llm_service, "ask_llm", AsyncMock(return_value="उत्तर")) as ask:
            response = await llm_service.generate_weather_response("कल बारिश?", {"forecast": []}, "hi")
        self.assertEqual(response, "उत्तर")
        self.assertIn(get_language_instruction("hi"), ask.await_args.args[0])


class MultilingualChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_explicit_language_is_used_and_persisted(self):
        session = "sprint12-api"
        clear_context(session)
        location = {"name": "Ahmedabad", "country": "India", "admin1": "Gujarat", "latitude": 23.02, "longitude": 72.57}
        query = {"intent": "forecast", "location": "Ahmedabad", "time": "tomorrow", "activity": None}
        with (
            patch.object(api, "save_chat_message", AsyncMock()),
            patch.object(api, "understand_with_llm", AsyncMock(return_value=query)),
            patch.object(api, "choose_weather_tool", AsyncMock(return_value={"tool": "forecast", "reason": "future"})),
            patch.object(api, "search_location", AsyncMock(return_value=[location])),
            patch.object(api, "get_forecast", AsyncMock(return_value={"daily": {}})),
            patch.object(api, "format_forecast", return_value=[]),
            patch.object(api, "generate_weather_response", AsyncMock(return_value="कल बारिश की संभावना है।")) as generate,
        ):
            response = await api.chat(api.ChatRequest(message="Ahmedabad mein kal baarish hogi?", session_id=session, language="hi"))
        self.assertEqual(response["understanding"]["location"], "Ahmedabad")
        self.assertEqual(response["understanding"]["time"], "tomorrow")
        self.assertEqual(get_context(session)["language"], "hi")
        self.assertEqual(generate.await_args.args[2], "hi")

    async def test_english_request_remains_compatible(self):
        request = api.ChatRequest(message="Hello", session_id="sprint12-english")
        with patch.object(api, "save_chat_message", AsyncMock()):
            response = await api.chat(request)
        self.assertEqual(response["tool"]["tool"], "conversation")
        self.assertEqual(response["language"], "en")


if __name__ == "__main__":
    unittest.main()
