"""Small, local multilingual helpers for the WeatherGPT accessibility layer."""

from __future__ import annotations

import re


SUPPORTED_LANGUAGES = {
    "en": "English", "hi": "Hindi", "gu": "Gujarati", "mr": "Marathi",
    "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
    "ml": "Malayalam", "pa": "Punjabi", "or": "Odia",
}

LANGUAGE_ALIASES = {
    "english": "en", "hindi": "hi", "gujarati": "gu", "marathi": "mr",
    "bengali": "bn", "bangla": "bn", "tamil": "ta", "telugu": "te",
    "kannada": "kn", "malayalam": "ml", "punjabi": "pa", "odia": "or",
    "oriya": "or",
}

# Unicode scripts are a deterministic, no-network signal.  Devanagari is
# intentionally reported as Hindi; callers can override it explicitly for Marathi.
SCRIPT_RANGES = {
    "hi": ("\u0900", "\u097f"), "gu": ("\u0a80", "\u0aff"),
    "bn": ("\u0980", "\u09ff"), "ta": ("\u0b80", "\u0bff"),
    "te": ("\u0c00", "\u0c7f"), "kn": ("\u0c80", "\u0cff"),
    "ml": ("\u0d00", "\u0d7f"), "pa": ("\u0a00", "\u0a7f"),
    "or": ("\u0b00", "\u0b7f"),
}

# This deliberately maps only common weather/time words for the rule-based
# fallback. Groq remains responsible for complete structured understanding.
CANONICAL_TERMS = {
    "hi": {"kal subah": "tomorrow morning", "kal shaam": "tomorrow evening", "kal": "tomorrow", "aaj": "today", "baarish": "rain", "mausam": "weather", "hogi": "will be"},
    "gu": {"કાલે": "tomorrow", "આજે": "today", "વરસાદ": "rain", "હવામાન": "weather", "માં": "in"},
    "mr": {"उद्या": "tomorrow", "आज": "today", "पाऊस": "rain", "हवामान": "weather", "मध्ये": "in"},
    "bn": {"আগামীকাল": "tomorrow", "আজ": "today", "বৃষ্টি": "rain", "আবহাওয়া": "weather"},
    "ta": {"நாளை": "tomorrow", "இன்று": "today", "மழை": "rain", "வானிலை": "weather"},
    "te": {"రేపు": "tomorrow", "నేడు": "today", "వర్షం": "rain", "వాతావరణం": "weather"},
    "kn": {"ನಾಳೆ": "tomorrow", "ಇಂದು": "today", "ಮಳೆ": "rain", "ಹವಾಮಾನ": "weather"},
    "ml": {"നാളെ": "tomorrow", "ഇന്ന്": "today", "മഴ": "rain", "കാലാവസ്ഥ": "weather"},
    "pa": {"ਕੱਲ੍ਹ": "tomorrow", "ਅੱਜ": "today", "ਮੀਂਹ": "rain", "ਮੌਸਮ": "weather"},
    "or": {"ଆସନ୍ତାକାଲି": "tomorrow", "ଆଜି": "today", "ବର୍ଷା": "rain", "ପାଣିପାଗ": "weather"},
}


def normalize_language(value: str | None) -> str | None:
    """Return a supported ISO-style code, or None for an invalid value."""
    if not value:
        return None
    candidate = value.strip().lower().replace("_", "-")
    candidate = candidate.split("-", 1)[0]
    candidate = LANGUAGE_ALIASES.get(candidate, candidate)
    return candidate if candidate in SUPPORTED_LANGUAGES else None


def is_supported_language(value: str | None) -> bool:
    return normalize_language(value) is not None


def get_language_name(code: str | None) -> str:
    return SUPPORTED_LANGUAGES.get(normalize_language(code) or "en", "English")


def detect_language(message: str) -> str | None:
    """Detect only clear scripts locally; ambiguous Latin text returns None."""
    for code, (start, end) in SCRIPT_RANGES.items():
        if any(start <= character <= end for character in message):
            return code
    return None


def resolve_response_language(explicit: str | None, message: str, session_language: str | None) -> str:
    """Explicit choice wins, then a confident script signal, then the session."""
    return normalize_language(explicit) or detect_language(message) or normalize_language(session_language) or "en"


def get_language_instruction(code: str | None) -> str:
    return f"Respond in {get_language_name(code)}."


def canonicalize_for_fallback(message: str, language: str | None) -> str:
    """Add canonical English weather terms for the existing fallback parser."""
    result = message
    for source, target in CANONICAL_TERMS.get(normalize_language(language) or "", {}).items():
        result = re.sub(re.escape(source), target, result, flags=re.IGNORECASE)
    return result


def extract_location_hint(message: str, language: str | None) -> str | None:
    """Recover a Latin-script city before a common Indian postposition.

    This is intentionally narrow: full multilingual place transliteration stays
    with the structured LLM path, while a reliable Hinglish city remains usable
    during an offline fallback.
    """
    if normalize_language(language) == "hi":
        match = re.search(r"\b([A-Za-z][A-Za-z .'-]*?)\s+(?:mein|me)\b", message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
