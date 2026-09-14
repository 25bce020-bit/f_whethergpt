import re


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
        "will it rain",
        "is it going to rain",
        "rain tomorrow"
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

    if "day after tomorrow" in text:
        time = "day_after_tomorrow"

    elif "tomorrow" in text:
        time = "tomorrow"

    elif "next 3 days" in text:
        time = "next_3_days"

    elif "next few days" in text:
        time = "next_few_days"

    elif "next week" in text:
        time = "next_week"

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

    # First try to extract a location after common location prepositions.
    #
    # Stop at:
    # - sentence punctuation
    # - common time expressions
    # - common question/action phrases
    #
    # This prevents cases like:
    # "in Ahmedabad. Is tomorrow suitable?"
    # from becoming:
    # "ahmedabad. is tomorrow suitable"
    patterns = [
        r"\b(?:in|at|near|around|from|to|of)\s+"
        r"(.+?)"
        r"(?=\s*[.!?]"
        r"|\s+(?:today|tomorrow|yesterday|now|currently|right now)\b"
        r"|\s+(?:day after tomorrow|next week|next few days|next 3 days)\b"
        r"|\s+(?:last week|last few days)\b"
        r"|\s+(?:for the next|for the last)\b"
        r"|$)",

        r"\bfor\s+"
        r"(.+?)"
        r"(?=\s*[.!?]"
        r"|\s+(?:today|tomorrow|yesterday|now|currently|right now)\b"
        r"|\s+(?:day after tomorrow|next week|next few days|next 3 days)\b"
        r"|\s+(?:last week|last few days)\b"
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

            # Reuse the same normalization used by the LLM path.
            from app.services.location_service import normalize_location_name

            location = normalize_location_name(candidate)

            if location:
                break
    # ----------------------------------------
    # Return structured query
    # ----------------------------------------

    return {
        "intent": intent,
        "location": location,
        "time": time,
        "original_message": message
    }
