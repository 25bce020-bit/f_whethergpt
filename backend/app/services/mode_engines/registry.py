"""Mode engine registry.

Routing decides the active mode. This registry only selects the processing
engine for an already-resolved active mode.
"""

from __future__ import annotations

from app.services.mode_service import WeatherMode
from .base_engine import BaseModeEngine
from .traveller_engine import traveller_engine


_MODE_ENGINES: dict[WeatherMode, BaseModeEngine] = {
    WeatherMode.TRAVELLER: traveller_engine,
}


def get_mode_engine(mode: WeatherMode | str) -> BaseModeEngine | None:
    """Return a specialized engine when one is implemented for the mode."""
    return _MODE_ENGINES.get(WeatherMode(mode))
