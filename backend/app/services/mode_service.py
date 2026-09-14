"""Mode selection and persona configuration for WeatherGPT chat requests."""

from dataclasses import dataclass
from enum import Enum
import re


class WeatherMode(str, Enum):
    NORMAL = "normal"
    FARMER = "farmer"
    RESEARCHER = "researcher"
    TRAVELLER = "traveller"


@dataclass(frozen=True)
class ModeConfiguration:
    name: str
    description: str
    persona_prompt: str


MODE_CONFIGURATIONS: dict[WeatherMode, ModeConfiguration] = {
    WeatherMode.NORMAL: ModeConfiguration(
        name="Normal Mode",
        description="Universal weather intelligence for everyday questions.",
        persona_prompt="Provide clear, practical general weather guidance.",
    ),
    WeatherMode.FARMER: ModeConfiguration(
        name="Farmer Mode",
        description="Weather framing for agricultural decisions.",
        persona_prompt=(
            "Frame supplied farmer_advisory data for an agricultural user. Use only "
            "the supplied weather facts and deterministic recommendations. Clearly "
            "separate official IMD warnings from WeatherGPT farmer advice. Never claim "
            "soil-moisture readings, crop maturity, chemical-specific instructions, or "
            "crop facts not present in the data."
        ),
    ),
    WeatherMode.RESEARCHER: ModeConfiguration(
        name="Researcher Mode",
        description="Structured analysis of retrieved weather observations, forecasts, and model output.",
        persona_prompt=(
            "Provide a concise research-style summary using only the supplied "
            "researcher_analysis and weather data. Clearly separate retrieved "
            "observations, forecast/model output, WeatherGPT-derived interpretation, "
            "and official IMD warnings. Do not invent measurements, confidence, "
            "long-term climate trends, causal conclusions, or scientific claims. "
            "State limitations when the supplied data is insufficient."
        ),
    ),
    WeatherMode.TRAVELLER: ModeConfiguration(
        name="Traveller Mode",
        description="Weather framing for trip and outdoor planning.",
        persona_prompt=(
            "Provide practical, concise, destination-aware travel and outdoor guidance using only "
            "the supplied traveller_advisory and weather data. Preserve the deterministic travel "
            "suitability status; do not invent temperature, rainfall, rain probability, warnings, "
            "road conditions, restrictions, attractions, itineraries, or booking details. Clearly "
            "separate official IMD warnings from WeatherGPT traveller advice and state limitations "
            "when weather or hourly data is unavailable."
        ),
    ),
}


@dataclass(frozen=True)
class ModeResolution:
    selected_mode: WeatherMode
    active_mode: WeatherMode
    display_mode: WeatherMode
    routing: str


def get_mode_configuration(mode: WeatherMode | str) -> ModeConfiguration:
    return MODE_CONFIGURATIONS[WeatherMode(mode)]


def resolve_selected_mode(
    requested_mode: WeatherMode | str | None,
    remembered_mode: WeatherMode | str | None = None,
    *,
    was_explicitly_supplied: bool = True,
) -> WeatherMode:
    """Respect an explicit request; otherwise retain a valid session selection."""
    if was_explicitly_supplied and requested_mode is not None:
        return WeatherMode(requested_mode)
    if remembered_mode is not None:
        return WeatherMode(remembered_mode)
    return WeatherMode.NORMAL


FARMER_ACTION_SIGNALS = re.compile(
    r"\b(irrigat(?:e|ion)|sow(?:ing)?|fertili[sz](?:e|er|ing)|pesticide|"
    r"spray(?:ing)?|harvest(?:ing)?|growth stage|field|farm(?:er|ing)?|"
    r"agricultur(?:e|al))\b"
)
FARMER_CROP_SIGNALS = re.compile(
    r"\b(crop(?:s)?|wheat|rice|paddy|cotton|tomato|maize|soybean|sugarcane)\b"
)
RESEARCHER_SIGNALS = re.compile(
    r"\b(gfs|open-meteo|wrf|nwp|numerical weather prediction|historical weather|"
    r"weather history|model comparison|compare (?:weather )?models?|forecast model|"
    r"model agreement|model disagreement|analy[sz]e|analysis|rainfall trend|"
    r"temperature trend|weather trend|research|study|observations)\b"
)
TRAVELLER_SIGNALS = re.compile(
    r"\b(travel(?:ling)?|traveller|traveler|trip|vacation|holiday|journey|"
    r"destination|sightseeing|tourism|tourist|outdoor activit(?:y|ies)|packing|"
    r"pack|raincoat)\b"
)
FARMER_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(irrigat(?:e|ion)|sow(?:ing)?|fertili[sz](?:e|er|ing)|pesticide|"
    r"spray(?:ing)?|harvest(?:ing)?|field)\b"
)
TRAVELLER_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(pack(?:ing)?|raincoat|umbrella|outdoor activit(?:y|ies)|"
    r"carry|departure)\b"
)
RESEARCHER_FOLLOW_UP_SIGNALS = re.compile(
    r"\b(model|agree(?:s|ment)?|disagree(?:ment)?|comparison|forecast confidence)\b"
)


def _recent_user_messages(context: dict | None) -> str:
    """Return only the small, existing session window used for routing context."""
    if not context:
        return ""
    return " ".join(
        str(item.get("user", "")) for item in context.get("history", [])[-6:]
        if isinstance(item, dict)
    ).lower()


def detect_automatic_mode(message: str, context: dict | None = None) -> WeatherMode:
    """Conservatively identify a specialized request without changing selection.

    A named destination and generic weather wording remain Normal.  Session context
    is used only for narrow follow-ups (for example, raincoat after a stated trip),
    never as a permanent preference or cross-session profile.
    """
    text = message.lower()
    if FARMER_ACTION_SIGNALS.search(text):
        return WeatherMode.FARMER
    # An explicit crop statement establishes the existing short-lived farmer context.
    if FARMER_CROP_SIGNALS.search(text) and re.search(r"\b(grow(?:ing)?|plant(?:ing)?)\b", text):
        return WeatherMode.FARMER
    if RESEARCHER_SIGNALS.search(text):
        return WeatherMode.RESEARCHER
    if TRAVELLER_SIGNALS.search(text):
        return WeatherMode.TRAVELLER

    history = _recent_user_messages(context)
    if context and context.get("crop") and FARMER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.FARMER
    if FARMER_CROP_SIGNALS.search(history) and FARMER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.FARMER
    if TRAVELLER_SIGNALS.search(history) and TRAVELLER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.TRAVELLER
    if context and context.get("research_tool") and RESEARCHER_FOLLOW_UP_SIGNALS.search(text):
        return WeatherMode.RESEARCHER
    return WeatherMode.NORMAL


def resolve_mode(
    message: str,
    selected_mode: WeatherMode | str,
    context: dict | None = None,
) -> ModeResolution:
    """Resolve active mode without ever mutating the selected/display mode."""
    selected = WeatherMode(selected_mode)
    # A user-selected specialist mode is authoritative.  Keep this early return
    # ahead of every automatic/context classifier so none can override it.
    if selected is not WeatherMode.NORMAL:
        return ModeResolution(
            selected_mode=selected,
            active_mode=selected,
            display_mode=selected,
            routing="manual",
        )

    active = detect_automatic_mode(message, context)
    return ModeResolution(
        selected_mode=selected,
        active_mode=active,
        display_mode=selected,
        routing="automatic",
    )
