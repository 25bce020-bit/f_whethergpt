from typing import Dict, Any


# Temporary in-memory conversation storage.
# This will later be replaced by PostgreSQL.
conversation_store: Dict[str, Dict[str, Any]] = {}


MAX_HISTORY = 6


def get_context(session_id: str) -> Dict[str, Any]:
    """
    Get conversation context for a session.
    """

    if session_id not in conversation_store:
        conversation_store[session_id] = {
            "location": None,
            "country": None,
            "state": None,
            "last_intent": None,
            "last_time": None,
            "language": None,
            "history": [],
        }

    return conversation_store[session_id]


def update_context(
    session_id: str,
    user_message: str,
    assistant_response: str,
    query: dict,
    location: dict | None = None,
    language: str | None = None,
):
    """
    Update conversation context after a successful request.
    """

    context = get_context(session_id)

    # Update location when available
    if location:
        context["location"] = location.get("name")
        context["country"] = location.get("country")
        context["state"] = location.get("state")

    # Update intent/time
    if query.get("intent"):
        context["last_intent"] = query.get("intent")

    if query.get("time"):
        context["last_time"] = query.get("time")

    if language or query.get("language"):
        context["language"] = language or query.get("language")

    # Store conversation history
    context["history"].append(
        {
            "user": user_message,
            "assistant": assistant_response,
        }
    )

    # Keep only recent messages
    context["history"] = context["history"][-MAX_HISTORY:]


def clear_context(session_id: str):
    """
    Clear a conversation session.
    """

    conversation_store.pop(session_id, None)
