"""Traveller Mode engine built on WeatherGPT's existing traveller service.

This engine intentionally does not fetch weather data itself. The shared chat
pipeline remains responsible for location resolution and weather/IMD retrieval.
The engine converts that supplied data into traveller-specific context.
"""

from __future__ import annotations

from typing import Any

from app.services.traveller_service import build_traveller_advisory, format_traveller_advisory
from .base_engine import BaseModeEngine


class TravellerEngine(BaseModeEngine):
    mode = "traveller"

    async def process(
        self,
        *,
        request_message: str,
        query: dict[str, Any],
        base_context: dict[str, Any],
    ) -> dict[str, Any]:
        del request_message  # Reserved for future travel-intent enrichment.

        advisory = build_traveller_advisory(
            destination=(base_context.get("location") or {}).get("name"),
            current_weather=base_context.get("current_weather"),
            forecast=base_context.get("forecast"),
            hourly_forecast=base_context.get("hourly_forecast"),
            imd_warnings=base_context.get("imd_warnings"),
            time_hint=query.get("time"),
        )

        return {
            "mode": self.mode,
            "traveller_advisory": advisory,
            "fallback_text": format_traveller_advisory(advisory),
        }


traveller_engine = TravellerEngine()
