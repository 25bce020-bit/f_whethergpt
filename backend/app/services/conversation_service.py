import re


CONVERSATION_RESPONSES = {
    "greeting": "Hello! How can I help with the weather today?",
    "small_talk": "I'm doing well, thanks for asking! What weather information can I help with?",
    "thanks": "You're welcome! Let me know if you need any weather information.",
    "goodbye": "Goodbye! Stay safe and have a great day.",
}


UNRELATED_RESPONSE = (
    "I'm WeatherGPT, so I'm best suited for weather, forecasts, alerts, "
    "climate, and weather-related advice."
)


def classify_conversation(message: str) -> str | None:
    """Classify short, non-weather conversational messages without an API call."""

    normalized = re.sub(r"[^a-z0-9\s']", " ", message.lower())
    normalized = " ".join(normalized.split())

    if not normalized:
        return None

    if normalized in {"hi", "hello", "hey", "hi there", "hello there", "hey there"}:
        return "greeting"

    if normalized in {
        "how are you",
        "how are you doing",
        "how r you",
        "what's up",
        "whats up",
        "sup",
        "wassup",
    }:
        return "small_talk"

    if normalized in {
        "good morning",
        "good afternoon",
        "good evening",
    }:
        return "greeting"

    if normalized in {
        "thanks",
        "thank you",
        "thanks a lot",
        "thank you so much",
        "thx",
    }:
        return "thanks"

    if normalized in {
        "bye",
        "goodbye",
        "bye bye",
        "see you",
        "see ya",
    }:
        return "goodbye"

    return None


def get_conversation_response(message: str) -> tuple[str, str] | None:
    """Return a response and intent for a recognized casual message."""

    intent = classify_conversation(message)

    if not intent:
        return None

    return intent, CONVERSATION_RESPONSES[intent]
