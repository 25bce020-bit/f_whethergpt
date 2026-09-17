"""Tests for multilingual language and script detection, Gujlish, Hinglish, Indic Unicode, and dynamic switching."""

import unittest

from app.services.language_service import (
    detect_language_and_script,
    get_language_instruction,
    resolve_response_language_and_script,
)
from app.services.mode_service import WeatherMode, resolve_mode
from app.services.query_service import understand_query


class MultilingualGujlishTests(unittest.TestCase):
    def test_gujlish_detection(self):
        cases = [
            "kale bapore tapman su che",
            "aaje ahmedabad nu weather kevu che?",
            "kale varsad padse?",
            "ahmedabad ma atyare ketlu tapman che?",
            "mari kheti mate kale nu havaman kevu rehse?",
            "kem cho? aaje tapman ketlu che?",
            "su chale che? varsad aavse?",
            "tamari kheti mate havaman kevu rehse?",
            "kale?",
        ]
        for message in cases:
            with self.subTest(message=message):
                lang, script = detect_language_and_script(message)
                self.assertEqual(lang, "gu", f"Expected 'gu' for '{message}', got '{lang}'")
                self.assertEqual(script, "latin", f"Expected 'latin' for '{message}', got '{script}'")

    def test_hinglish_detection(self):
        cases = [
            "ahmedabad me aaj mausam kaisa hai?",
            "mujhe kal ka mausam batao",
            "aaj mausam kaisa hai",
            "kya kal baarish hogi?",
            "delhi me tapman kitna hai?",
            "meri fasal ke liye kal ka mausam kaisa rahega?",
        ]
        for message in cases:
            with self.subTest(message=message):
                lang, script = detect_language_and_script(message)
                self.assertEqual(lang, "hi", f"Expected 'hi' for '{message}', got '{lang}'")
                self.assertEqual(script, "latin", f"Expected 'latin' for '{message}', got '{script}'")

    def test_indic_unicode_detection(self):
        cases = [
            ("અમદાવાદમાં આજે હવામાન કેવું છે?", "gu", "native"),
            ("કાલે વરસાદ પડશે?", "gu", "native"),
            ("કાલે?", "gu", "native"),
            ("अहमदाबाद में आज मौसम कैसा है?", "hi", "native"),
            ("कल बारिश होगी?", "hi", "native"),
            ("कल?", "hi", "native"),
            ("आज আহমেদাবাদের আবহাওয়া কেমন?", "bn", "native"),
            ("அகமதாபாத்தில் இன்று வானிலை எப்படி உள்ளது?", "ta", "native"),
            ("అహ్మదాబాద్‌లో నేడు వాతావరణం ఎలా ఉంది?", "te", "native"),
            ("ಅಹಮದಾಬಾದ್‌ನಲ್ಲಿ ಇಂದು ಹವಾಮಾನ ಹೇಗಿದೆ?", "kn", "native"),
            ("അഹമ്മദാബാദിൽ ഇന്ന് കാലാവസ്ഥ എങ്ങനെയുണ്ട്?", "ml", "native"),
            ("ਅਹਿਮਦਾਬਾਦ ਵਿੱਚ ਅੱਜ ਮੌਸਮ ਕਿਹੋ ਜਿਹਾ ਹੈ?", "pa", "native"),
            ("ଅହମ୍ମଦାବାଦରେ ଆଜି ପାଣିପାଗ କିପରି ଅଛି?", "or", "native"),
            ("अहमदाबादमध्ये आज हवामान कसे आहे?", "mr", "native"),
        ]
        for message, expected_lang, expected_script in cases:
            with self.subTest(message=message):
                lang, script = detect_language_and_script(message)
                self.assertEqual(lang, expected_lang, f"Expected '{expected_lang}' for '{message}', got '{lang}'")
                self.assertEqual(script, expected_script, f"Expected '{expected_script}' for '{message}', got '{script}'")

    def test_english_detection(self):
        cases = [
            "What is the weather in Ahmedabad?",
            "Will it rain tomorrow in Mumbai?",
            "What is forecast for next three hours?",
            "How windy will it be tonight?",
            "Should I irrigate my wheat crop tomorrow?",
            "Tomorrow?",
        ]
        for message in cases:
            with self.subTest(message=message):
                lang, script = detect_language_and_script(message)
                self.assertEqual(lang, "en", f"Expected 'en' for '{message}', got '{lang}'")
                self.assertEqual(script, "latin", f"Expected 'latin' for '{message}', got '{script}'")

    def test_language_instructions(self):
        gujlish_inst = get_language_instruction("gu", "latin")
        self.assertIn("Gujlish", gujlish_inst)
        self.assertIn("Latin/Roman", gujlish_inst)
        self.assertIn("Do NOT switch to English", gujlish_inst)

        hinglish_inst = get_language_instruction("hi", "latin")
        self.assertIn("Roman Hindi", hinglish_inst)
        self.assertIn("Latin/Roman", hinglish_inst)

        gu_unicode_inst = get_language_instruction("gu", "native")
        self.assertIn("ગુજરાતી", gu_unicode_inst)

        hi_unicode_inst = get_language_instruction("hi", "native")
        self.assertIn("हिन्दी", hi_unicode_inst)

        mr_unicode_inst = get_language_instruction("mr", "native")
        self.assertIn("मराठी", mr_unicode_inst)

        ta_unicode_inst = get_language_instruction("ta", "native")
        self.assertIn("தமிழ்", ta_unicode_inst)

        bn_unicode_inst = get_language_instruction("bn", "native")
        self.assertIn("বাংলা", bn_unicode_inst)

    def test_dynamic_per_message_language_switching(self):
        # 4-step sequence
        msg1 = "What is the weather in Ahmedabad?"
        lang1, script1 = resolve_response_language_and_script(None, msg1, None)
        self.assertEqual((lang1, script1), ("en", "latin"))

        msg2 = "kale varsad padse?"
        lang2, script2 = resolve_response_language_and_script(None, msg2, lang1)
        self.assertEqual((lang2, script2), ("gu", "latin"))

        msg3 = "કાલે વરસાદ પડશે?"
        lang3, script3 = resolve_response_language_and_script(None, msg3, lang2)
        self.assertEqual((lang3, script3), ("gu", "native"))

        msg4 = "will it rain tomorrow?"
        lang4, script4 = resolve_response_language_and_script(None, msg4, lang3)
        self.assertEqual((lang4, script4), ("en", "latin"))

    def test_mode_routing_with_multilingual_queries(self):
        # Gujlish + Farmer
        farmer_gujlish = "mari kheti mate kale nu havaman kevu rehse?"
        mode1 = resolve_mode(farmer_gujlish, "normal")
        lang1, script1 = detect_language_and_script(farmer_gujlish)
        self.assertEqual(mode1.active_mode, WeatherMode.FARMER)
        self.assertEqual((lang1, script1), ("gu", "latin"))

        # Hindi Unicode + Farmer
        farmer_hindi = "मेरी गेहूं की फसल के लिए कल का मौसम कैसा रहेगा?"
        mode2 = resolve_mode(farmer_hindi, "normal")
        lang2, script2 = detect_language_and_script(farmer_hindi)
        self.assertEqual(mode2.active_mode, WeatherMode.FARMER)
        self.assertEqual((lang2, script2), ("hi", "native"))

        # Bengali + Traveller
        traveller_bengali = "আগামীকাল ভ্রমণের জন্য আবহাওয়া কেমন?"
        mode3 = resolve_mode(traveller_bengali, "normal")
        lang3, script3 = detect_language_and_script(traveller_bengali)
        self.assertEqual((lang3, script3), ("bn", "native"))

    def test_query_parser_does_not_treat_temporal_or_questions_as_locations(self):
        queries = [
            "what is forecast for next three hours",
            "Will it rain tomorrow?",
            "How windy will it be tonight?",
            "What about next 24 hours?",
            "what is the weather today",
        ]
        for q in queries:
            with self.subTest(query=q):
                parsed = understand_query(q)
                self.assertIsNone(parsed.get("location"), f"Location should be None for '{q}', got '{parsed.get('location')}'")


if __name__ == "__main__":
    unittest.main()
