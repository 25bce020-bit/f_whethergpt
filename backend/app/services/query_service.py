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

    if any(phrase in text for phrase in [
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

    patterns = [
        # "in Ahmedabad"
        r"\bin\s+(.+?)(?=\s+(?:today|tomorrow|yesterday|now|currently|right now|day after tomorrow|next week|next few days|next 3 days|last week|last few days)\b|\s+for\s+(?:the\s+)?(?:next|last)\b|\?|$)",

        # "at Ahmedabad"
        r"\bat\s+(.+?)(?=\s+(?:today|tomorrow|yesterday|now|currently|right now|day after tomorrow|next week|next few days|next 3 days|last week|last few days)\b|\s+for\s+(?:the\s+)?(?:next|last)\b|\?|$)",

        # "for Ahmedabad"
        r"\bfor\s+(.+?)(?=\s+(?:today|tomorrow|yesterday|now|currently|right now|day after tomorrow|next week|next few days|next 3 days|last week|last few days)\b|\?|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            location = match.group(1).strip()
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