import unittest

from app.services.conversation_service import (
    UNRELATED_RESPONSE,
    get_conversation_response,
)


class ConversationRoutingTests(unittest.TestCase):
    def test_recognizes_casual_conversation(self):
        cases = {
            "Hi": "greeting",
            "hello!": "greeting",
            "Hey there": "greeting",
            "How are you?": "small_talk",
            "What's up?": "small_talk",
            "sup": "small_talk",
            "Good morning": "greeting",
            "Good afternoon": "greeting",
            "Good evening": "greeting",
            "Thanks": "thanks",
            "Thank you so much": "thanks",
            "Bye": "goodbye",
            "Goodbye": "goodbye",
        }

        for message, intent in cases.items():
            with self.subTest(message=message):
                result = get_conversation_response(message)
                self.assertIsNotNone(result)
                self.assertEqual(result[0], intent)
                self.assertTrue(result[1])

    def test_unrelated_questions_are_not_casual_conversation(self):
        for message in [
            "What is the capital of France?",
            "Explain quantum computing.",
            "Solve 2 + 2.",
        ]:
            with self.subTest(message=message):
                self.assertIsNone(get_conversation_response(message))

        self.assertIn("weather, forecasts, alerts, climate", UNRELATED_RESPONSE)

    def test_weather_questions_are_not_casual_conversation(self):
        for message in [
            "What's the weather in Delhi?",
            "Will it rain tomorrow in Mumbai?",
            "Show the GFS forecast for Pune.",
            "Is there an IMD warning for Ahmedabad?",
        ]:
            with self.subTest(message=message):
                self.assertIsNone(get_conversation_response(message))
