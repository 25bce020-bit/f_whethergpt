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
            "Frame the available weather information for an agricultural user. "
            "Do not claim crop-specific analysis or recommendations not present in the data."
        ),
    ),
    WeatherMode.RESEARCHER: ModeConfiguration(
        name="Researcher Mode",
        description="Weather framing for technical and scientific analysis.",
        persona_prompt=(
            "Use precise, analytical weather language while remaining limited to "
            "the supplied data. Do not invent scientific analysis."
        ),
    ),
    WeatherMode.TRAVELLER: ModeConfiguration(
        name="Traveller Mode",
        description="Weather framing for trip and outdoor planning.",
        persona_prompt=(
            "Frame the available weather information for travel and outdoor planning. "
            "Do not invent itinerary or booking details."
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


def detect_automatic_mode(message: str) -> WeatherMode:
    """Conservatively identify clearly specialized weather contexts.

    This deliberately uses explicit context signals rather than broad words such as
    "rain" or "forecast", so ordinary weather questions stay in Normal mode.
    """
    text = message.lower()
    if re.search(r"\b(irrigat(?:e|ion)|crop(?:s)?|wheat|paddy|soil|farm(?:er|ing)?|harvest|sow(?:ing)?)\b", text):
        return WeatherMode.FARMER
    if re.search(r"\b(gfs|wrf|nwp|numerical weather|meteorological analysis|model comparison|compare (?:weather )?models?|forecast model)\b", text):
        return WeatherMode.RESEARCHER
    if re.search(r"\b(travel(?:ling)?|travelling|trip|destination|itinerary|vacation|holiday|outdoor trip)\b", text):
        return WeatherMode.TRAVELLER
    return WeatherMode.NORMAL


def resolve_mode(
    message: str,
    selected_mode: WeatherMode | str,
) -> ModeResolution:
    """Resolve active mode without ever mutating the selected/display mode."""
    selected = WeatherMode(selected_mode)
    active = detect_automatic_mode(message) if selected is WeatherMode.NORMAL else selected
    return ModeResolution(
        selected_mode=selected,
        active_mode=active,
        display_mode=selected,
        routing="automatic" if selected is WeatherMode.NORMAL else "manual",
    )
