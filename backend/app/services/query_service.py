import re

NON_LOCATION_WORDS = {
    "the", "a", "an", "this", "that", "these", "those", "my", "our", "your",
    "his", "her", "their", "its", "some", "any", "all", "me", "us", "it",
    "in", "at", "for", "to", "from", "of", "on", "with", "by", "about",
    "what", "when", "how", "where", "which", "why", "who", "whom", "whose",
    "is", "are", "was", "were", "will", "would", "can", "could", "shall",
    "should", "may", "might", "must", "do", "does", "did", "have", "has",
    "had", "be", "been", "being",
    "weather", "forecast", "prediction", "rain", "rainfall", "rainy",
    "temperature", "temp", "climate", "warning", "alert", "condition",
    "conditions", "hot", "cold", "wind", "humidity", "clouds", "cloudy",
    "next", "last", "past", "future", "upcoming", "coming", "previous",
    "current", "today", "tomorrow", "yesterday", "tonight", "now", "currently",
    "hour", "hours", "hr", "hrs", "minute", "minutes", "min", "mins",
    "day", "days", "week", "weeks", "month", "months", "year", "years",
    "morning", "afternoon", "evening", "night", "weekend",
    "few", "couple", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
}

TEMPORAL_PATTERNS = [
    r"^(?:the\s+)?(?:next|last|past|upcoming|coming|this|previous)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|few|couple\s+of)?\s*(?:hours?|hrs?|days?|weeks?|months?|years?|morning|afternoon|evening|night|weekend)\b",
    r"^(?:next|last|this)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    r"^(?:today|tomorrow|yesterday|tonight|now|currently|right\s+now|day\s+after\s+tomorrow)\b",
    r"\b(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?)\b",
    r"^(?:what|when|how|where|which|why|is|will|can|could|would|should|do|does|did)\b",
    r"^(?:forecast|weather|rain|temperature|temp|climate|warning|alert|condition|conditions)\b",
]


def is_temporal_or_query_phrase(candidate: str) -> bool:
    cleaned = candidate.lower().strip()
    if not cleaned:
        return True
    
    # Strip leading articles
    core = re.sub(r"^(?:the|a|an)\s+", "", cleaned).strip()
    if core in NON_LOCATION_WORDS or cleaned in NON_LOCATION_WORDS:
        return True

    for pat in TEMPORAL_PATTERNS:
        if re.search(pat, cleaned) or re.search(pat, core):
            return True

    # If it consists entirely of non-location words
    words = core.split()
    if words and all(w in NON_LOCATION_WORDS for w in words):
        return True

    return False


def understand_query(message: str) -> dict:

    text = message.lower().strip()

    # ----------------------------------------
    # Detect intent
    # ----------------------------------------
    if any(word in text for word in [
        "yesterday",
        "last week",
        "last few days",
        "historical",
        "history",
        "past weather",
        "previous weather" 
    ]):
        intent = "historical"

    elif any(phrase in text for phrase in [
        "average temperature",
        "average rainfall",
        "average weather",
        "climate",
        "climate trend",
        "temperature trend",
        "weather trend"
    ]):
        intent = "climate"    

    elif any(word in text for word in [
        "alert",
        "warning",
        "danger",
        "risk",
        "advisory",
        "severe weather",
        "extreme weather"
    ]):
        intent = "advisory"

    elif any(phrase in text for phrase in [
        "forecast",
        "prediction",
        "tomorrow",
        "day after tomorrow",
        "next week",
        "next few days",
        "next 3 days",
        "next three days",
        "next 3 hours",
        "next three hours",
        "next few hours",
        "next 24 hours",
        "next 48 hours",
        "next hours",
        "tonight",
        "will it rain",
        "is it going to rain",
        "rain tomorrow",
        "rain today",
        "what about tomorrow"
    ]):
        intent = "forecast"

    elif any(word in text for word in [
        "weather",
        "temperature",
        "temp",
        "hot",
        "cold",
        "rain",
        "rainfall",
        "wind",
        "humidity",
        "cloud",
        "cloudy"
    ]):
        intent = "current_weather"

    else:
        intent = "unknown"

    # ----------------------------------------
    # Detect time
    # ----------------------------------------

    if any(p in text for p in [
        "next 3 hours",
        "next three hours",
        "next few hours",
        "next couple of hours",
        "in the next 3 hours",
        "in the next three hours",
        "in the next few hours",
        "next 3 hrs",
        "next three hrs"
    ]):
        time = "next_3_hours"

    elif any(p in text for p in ["next 24 hours", "next 24 hrs"]):
        time = "next_24_hours"

    elif any(p in text for p in ["next 48 hours", "next 48 hrs"]):
        time = "next_48_hours"

    elif "day after tomorrow morning" in text:
        time = "day_after_tomorrow_morning"

    elif "day after tomorrow" in text:
        time = "day_after_tomorrow"

    elif "tomorrow morning" in text:
        time = "tomorrow_morning"

    elif "tomorrow afternoon" in text:
        time = "tomorrow_afternoon"

    elif "tomorrow evening" in text:
        time = "tomorrow_evening"

    elif "tomorrow" in text:
        time = "tomorrow"

    elif "next 3 days" in text or "next three days" in text:
        time = "next_3_days"

    elif "next few days" in text:
        time = "next_few_days"

    elif "next week" in text:
        time = "next_week"

    elif "tonight" in text:
        time = "tonight"

    elif "yesterday" in text:
        time = "yesterday"

    elif "last week" in text:
        time = "last_week"

    elif "last few days" in text:
        time = "last_few_days"

    elif "today" in text:
        time = "today"

    elif "now" in text or "currently" in text or "right now" in text:
        time = "now"

    else:
        time = "unspecified"

    # ----------------------------------------
    # Detect location
    # ----------------------------------------

    location = None

    patterns = [
        r"\b(?:in|at|near|around|from|to|of)\s+"
        r"([a-z][a-z .'-]*?)"
        r"(?=\s*[.!?]"
        r"|\s+(?:today|tomorrow|yesterday|now|currently|right now)\b"
        r"|\s+(?:day after tomorrow|next|last|this)\b"
        r"|\s+(?:for\s+(?:the\s+)?next|for\s+(?:the\s+)?last|in\s+the|over\s+(?:the\s+)?next|over\s+(?:the\s+)?last|over\s+the)\b"
        r"|$)",

        r"\bfor\s+"
        r"([a-z][a-z .'-]*?)"
        r"(?=\s*[.!?]"
        r"|\s+(?:today|tomorrow|yesterday|now|currently|right now)\b"
        r"|\s+(?:day after tomorrow|next|last|this)\b"
        r"|\s+(?:for\s+(?:the\s+)?next|for\s+(?:the\s+)?last|in\s+the|over\s+(?:the\s+)?next|over\s+(?:the\s+)?last|over\s+the)\b"
        r"|$)",

        # Research-style wording: "Analyze Ahmedabad weather tomorrow".
        r"\b(?:analy[sz]e|compare|study)\s+"
        r"([a-z][a-z .'-]*?)"
        r"\s+(?:weather|forecast|climate|rainfall|temperature|history)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if match:
            candidate = match.group(1).strip()
            candidate = re.sub(r"\s+instead$", "", candidate, flags=re.IGNORECASE)

            if is_temporal_or_query_phrase(candidate):
                continue

            # Reuse the same normalization used by the LLM path.
            from app.services.location_service import normalize_location_name

            location = normalize_location_name(candidate)

            if location and not is_temporal_or_query_phrase(location):
                break
            else:
                location = None

    # ----------------------------------------
    # Return structured query
    # ----------------------------------------

    return {
        "intent": intent,
        "location": location,
        "time": time,
        "original_message": message
    }
