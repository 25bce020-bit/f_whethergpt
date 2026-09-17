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
    "oriya": "or", "gujlish": "gu", "hinglish": "hi",
}

# Unicode scripts are a deterministic, no-network signal.
SCRIPT_RANGES = {
    "gu": ("\u0a80", "\u0aff"),
    "bn": ("\u0980", "\u09ff"),
    "ta": ("\u0b80", "\u0bff"),
    "te": ("\u0c00", "\u0c7f"),
    "kn": ("\u0c80", "\u0cff"),
    "ml": ("\u0d00", "\u0d7f"),
    "pa": ("\u0a00", "\u0a7f"),
    "or": ("\u0b00", "\u0b7f"),
    "hi": ("\u0900", "\u097f"),
}

# Distinctive Marathi markers in Devanagari script to distinguish Marathi from Hindi
MARATHI_DEVANAGARI_MARKERS = [
    "मध्ये", "कसे", "कशी", "कसा", "आहे", "नाही", "पाऊस", "उद्या", "हवामान",
    "सांगा", "काय", "होणार", "आहोत", "आहेत", "करा", "पडेल", "येईल", "तापमान"
]

# Lexical tokens for Latin-script Indic languages
GUJLISH_WORDS = {
    "kale", "kaale", "aaje", "aje", "bapore", "bapor", "savare", "sanje",
    "raate", "ratre", "paramdivse", "varsad", "varshadh", "tapman", "taapman",
    "havaman", "havaaman", "thandi", "garmi", "dhukhas", "vavazodu", "pavan",
    "maru", "mari", "maro", "tamaru", "tamari", "tamaro", "aapnu", "aapna",
    "kem", "cho", "su", "shu", "che", "chhe", "nathi", "ane", "mate",
    "ma", "maa", "nu", "ni", "no", "na", "mathi", "sathe", "pasi", "pachi",
    "padse", "padshe", "rehse", "rehshe", "thase", "thashe", "aavse", "aavshe",
    "chale", "chalse", "batavo", "janavo", "aapo", "lagse", "jovu", "karo",
    "karjo", "kevu", "kevi", "kevo", "keva", "ketlu", "ketla", "ketli",
    "kyare", "kya", "kona", "kheti", "khedut", "atyare", "atyar", "hava", "gam", "gamda",
    "khatar", "vapru", "vapravu", "asar", "ghau", "ghav", "pak", "nuksan", "faydo", "vavetar", "sinchai",
}

HINGLISH_WORDS = {
    "aaj", "kal", "parso", "subah", "dopahar", "shaam", "sham", "raat",
    "hona", "hogi", "hoga", "honge", "mausam", "mosam", "baarish", "barish",
    "barsat", "sardi", "thand", "hawa", "toofan", "tufan", "mera", "meri",
    "mere", "aapka", "aapki", "aapke", "tera", "teri", "kya", "kyu", "kyon",
    "kaise", "kaisa", "kaisi", "kitna", "kitni", "kitne", "kab", "kaha",
    "kahan", "hai", "hain", "tha", "thi", "nahi", "nahin",
    "aur", "ya", "lekin", "mein", "liye", "keliye", "batao", "bataye",
    "bataiye", "padega", "padegi", "karega", "karegi", "dekhna", "kariye",
    "rahega", "rahegi", "khet", "kisan", "fasal", "mujhe", "hume", "humko",
}

ROMAN_MARATHI_WORDS = {
    "udya", "paus", "kasa", "kase", "kashi", "aahe", "ahet", "nahi",
    "sanga", "majha", "majhi", "tujha", "tujhi", "aamcha", "aamchi", "kiti",
}

ENGLISH_WORDS = {
    "what", "when", "how", "where", "which", "why", "who", "whom", "whose",
    "is", "are", "was", "were", "will", "would", "shall", "should", "can",
    "could", "may", "might", "must", "do", "does", "did", "have", "has", "had",
    "the", "this", "that", "these", "those", "a", "an", "and", "or", "but",
    "in", "at", "to", "for", "from", "of", "with", "by", "about", "into",
    "weather", "forecast", "temperature", "rain", "rainfall", "rainy", "wind",
    "windy", "humidity", "hot", "cold", "today", "tomorrow", "tonight", "yesterday",
    "now", "currently", "next", "last", "hour", "hours", "day", "days", "week",
    "weeks", "please", "tell", "show", "give", "me", "my", "your", "its", "our",
    "crop", "crops", "wheat", "farm", "farming", "farmer", "field", "irrigate",
    "irrigation", "travel", "travelling", "trip", "going", "suitable",
}

# Canonical terms for offline rule-based fallback
CANONICAL_TERMS = {
    "hi": {"kal subah": "tomorrow morning", "kal shaam": "tomorrow evening", "kal": "tomorrow", "aaj": "today", "baarish": "rain", "mausam": "weather", "hogi": "will be"},
    "gu": {"કાલે": "tomorrow", "આજે": "today", "વરસાદ": "rain", "હવામાન": "weather", "માં": "in", "kale": "tomorrow", "aaje": "today", "varsad": "rain", "havaman": "weather", "tapman": "temperature"},
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


def detect_language_and_script(message: str) -> tuple[str, str]:
    """Detect language and script from user message.

    Returns:
        (language_code, script_type) where script_type is 'native' or 'latin'.
    """
    if not message or not message.strip():
        return "en", "latin"

    # 1. Check Indic Unicode scripts
    for code, (start, end) in SCRIPT_RANGES.items():
        if any(start <= character <= end for character in message):
            if code == "hi":
                # Check for Marathi markers in Devanagari
                if any(marker in message for marker in MARATHI_DEVANAGARI_MARKERS):
                    return "mr", "native"
                return "hi", "native"
            return code, "native"

    # 2. Check for Latin-script transliterations (Gujlish, Hinglish, Roman Marathi, English)
    tokens = re.findall(r"\b[a-z']+\b", message.lower())
    if not tokens:
        return "en", "latin"

    gujlish_score = sum(1 for token in tokens if token in GUJLISH_WORDS)
    hinglish_score = sum(1 for token in tokens if token in HINGLISH_WORDS)
    marathi_score = sum(1 for token in tokens if token in ROMAN_MARATHI_WORDS)
    english_score = sum(1 for token in tokens if token in ENGLISH_WORDS)

    # Specific Gujarati question / verbal phrases
    if any(phrase in message.lower() for phrase in [
        "su che", "shu che", "kevu che", "kevu rehse", "kevu rehes",
        "varsad padse", "tapman su", "tapman ketlu", "kem cho", "su chale",
        "nu weather", "nu havaman", "mate kale", "kheti mate",
    ]):
        gujlish_score += 3

    # Specific Hindi question / verbal phrases
    if any(phrase in message.lower() for phrase in [
        "kaisa hai", "kaisa hoga", "kaisa rahega", "baarish hogi", "barish hogi",
        "mausam kaisa", "kitna tapman", "kya mausam", "me aaj", "ka mausam",
    ]):
        hinglish_score += 3

    # If Indic signals dominate
    if gujlish_score > 0 and gujlish_score >= english_score and gujlish_score >= hinglish_score and gujlish_score >= marathi_score:
        return "gu", "latin"

    if hinglish_score > 0 and hinglish_score >= english_score and hinglish_score > gujlish_score and hinglish_score >= marathi_score:
        return "hi", "latin"

    if marathi_score > 0 and marathi_score >= english_score and marathi_score > gujlish_score and marathi_score > hinglish_score:
        return "mr", "latin"

    return "en", "latin"


def detect_language(message: str) -> str | None:
    """Backward-compatible helper returning language code only."""
    lang, _ = detect_language_and_script(message)
    return lang if lang != "en" else None


def resolve_response_language_and_script(
    explicit: str | None,
    message: str,
    session_language: str | None,
) -> tuple[str, str]:
    """Determine response language and script.

    The current user message's language and script take highest precedence
    for automatic language matching.
    """
    # Detect from current message
    detected_lang, detected_script = detect_language_and_script(message)

    # If message had a clear Indic Unicode script or Latin Indic transliteration, use it
    if detected_lang != "en" or detected_script != "latin":
        return detected_lang, detected_script

    # If explicit language was given (and it is not generic default 'en' when message is english)
    normalized_explicit = normalize_language(explicit)
    if normalized_explicit and normalized_explicit != "en":
        return normalized_explicit, "native"

    # Default to English in Latin script
    return "en", "latin"


def resolve_response_language(
    explicit: str | None,
    message: str,
    session_language: str | None,
) -> str:
    """Backward-compatible helper returning language code."""
    lang, _ = resolve_response_language_and_script(explicit, message, session_language)
    return lang


def get_language_instruction(code: str | None, script: str = "native") -> str:
    """Generate precise language and script instruction for LLM prompts."""
    lang = normalize_language(code) or "en"
    lang_name = get_language_name(lang)

    if lang == "gu" and script == "latin":
        return (
            "The user is writing in Gujarati using Latin/Roman script (Gujlish / Roman Gujarati). "
            "Respond in natural, fluent conversational Gujarati using Latin/Roman characters "
            "(e.g., 'aaje Ahmedabad nu weather saaf rehse ane tapman lagbhag 28°C rehse.', 'kale varsad padvani sambhavna che.'). "
            "Do NOT switch to English. Do NOT convert the response into Gujarati Unicode script unless explicitly requested. "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "hi" and script == "latin":
        return (
            "The user is writing in Hindi using Latin/Roman script (Roman Hindi / Hinglish). "
            "Respond in natural, fluent conversational Hindi using Latin/Roman characters "
            "(e.g., 'aaj Ahmedabad me mausam saaf rahega aur tapman lagbhag 28°C hoga.'). "
            "Do NOT switch to English. Do NOT convert the response into Devanagari script unless explicitly requested. "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "mr" and script == "latin":
        return (
            "The user is writing in Marathi using Latin/Roman script (Roman Marathi). "
            "Respond in natural conversational Marathi using Latin/Roman characters. "
            "Do NOT switch to English. Keep numerical weather values, °C units, and factual information accurate."
        )

    if lang == "gu":
        return (
            "The user is writing in Gujarati using Gujarati script. "
            "Respond in natural Gujarati using Gujarati script (ગુજરાતી). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "hi":
        return (
            "The user is writing in Hindi using Devanagari script. "
            "Respond in natural Hindi using Devanagari script (हिन्दी). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "mr":
        return (
            "The user is writing in Marathi using Devanagari script. "
            "Respond in natural Marathi using Devanagari script (मराठी). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "bn":
        return (
            "The user is writing in Bengali using Bengali script. "
            "Respond in natural Bengali using Bengali script (বাংলা). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "ta":
        return (
            "The user is writing in Tamil using Tamil script. "
            "Respond in natural Tamil using Tamil script (தமிழ்). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "te":
        return (
            "The user is writing in Telugu using Telugu script. "
            "Respond in natural Telugu using Telugu script (తెలుగు). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "kn":
        return (
            "The user is writing in Kannada using Kannada script. "
            "Respond in natural Kannada using Kannada script (ಕನ್ನಡ). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "ml":
        return (
            "The user is writing in Malayalam using Malayalam script. "
            "Respond in natural Malayalam using Malayalam script (മലയാളം). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "pa":
        return (
            "The user is writing in Punjabi using Gurmukhi script. "
            "Respond in natural Punjabi using Gurmukhi script (ਪੰਜਾਬੀ). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    if lang == "or":
        return (
            "The user is writing in Odia using Odia script. "
            "Respond in natural Odia using Odia script (ଓଡ଼ିଆ). "
            "Keep numerical weather values, °C units, numbers, and factual information accurate."
        )

    return f"Respond in {lang_name}."


def canonicalize_for_fallback(message: str, language: str | None) -> str:
    """Add canonical English weather terms for the existing fallback parser."""
    result = message
    for source, target in CANONICAL_TERMS.get(normalize_language(language) or "", {}).items():
        result = re.sub(re.escape(source), target, result, flags=re.IGNORECASE)
    return result


def extract_location_hint(message: str, language: str | None) -> str | None:
    """Recover a Latin-script city before a common Indian postposition.

    Supports Hindi (mein/me/se), Gujarati (ma/maa/nu/ni/mate), and general patterns.
    """
    lang = normalize_language(language)
    if lang == "hi":
        match = re.search(r"\b([A-Za-z][A-Za-z .'-]*?)\s+(?:mein|me|se)\b", message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    elif lang == "gu":
        match = re.search(r"\b([A-Za-z][A-Za-z .'-]*?)\s+(?:ma|maa|nu|ni|mate)\b", message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

