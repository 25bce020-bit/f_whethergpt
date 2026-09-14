from typing import Dict, Any


# Temporary in-memory conversation storage.
# This will later be replaced by PostgreSQL.
conversation_store: Dict[str, Dict[str, Any]] = {}


MAX_HISTORY = 6


def relevant_context(context: Dict[str, Any], active_mode: str) -> Dict[str, Any]:
    """Return only the session facts that may inform this request.

    This is deliberately a small, deterministic projection rather than a profile
    dump.  It is safe to pass to the LLM because every value originated in this
    session and was explicitly captured by the backend.
    """
    general = {
        key: context.get(key)
        for key in ("location", "country", "state", "last_intent", "last_time")
    }
    if active_mode == "farmer":
        return {**general, "crop": context.get("crop"), "growth_stage": context.get("growth_stage")}
    if active_mode == "traveller":
        return {
            "destination": context.get("destination"),
            "travel_time": context.get("travel_time"),
            # Location is included only as a fallback for sessions created before
            # destination context, not as unrelated farmer/researcher state.
            "location": context.get("destination") or context.get("location"),
            "last_intent": context.get("last_intent"),
            "last_time": context.get("last_time"),
        }
    if active_mode == "researcher":
        return {
            "location": context.get("research_location") or context.get("location"),
            "research_location": context.get("research_location"),
            "research_time": context.get("research_time"),
            "research_tool": context.get("research_tool"),
            "last_intent": context.get("last_intent"),
            "last_time": context.get("last_time"),
        }
    return general


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
            "selected_mode": "normal",
            "last_active_mode": "normal",
            "crop": None,
            "growth_stage": None,
            "destination": None,
            "travel_time": None,
            "research_location": None,
            "research_time": None,
            "research_tool": None,
            "history": [],
        }

    return conversation_store[session_id]


def update_context(
    session_id: str,
    user_message: str,
    assistant_response: str,
    query: dict,
    location: dict | None = None,
    selected_mode: str | None = None,
    last_active_mode: str | None = None,
    crop: str | None = None,
    growth_stage: str | None = None,
    destination: str | None = None,
    travel_time: str | None = None,
    research_location: str | None = None,
    research_time: str | None = None,
    research_tool: str | None = None,
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

    if selected_mode is not None:
        context["selected_mode"] = selected_mode

    if last_active_mode is not None:
        context["last_active_mode"] = last_active_mode

    # Farmer details are intentionally session-scoped; they are not a user profile.
    if crop is not None:
        context["crop"] = crop

    if growth_stage is not None:
        context["growth_stage"] = growth_stage

    if destination is not None:
        context["destination"] = destination
    if travel_time is not None:
        context["travel_time"] = travel_time
    if research_location is not None:
        context["research_location"] = research_location
    if research_time is not None:
        context["research_time"] = research_time
    if research_tool is not None:
        context["research_tool"] = research_tool

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
