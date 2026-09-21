"""Traveller API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TravellerRoutesRequest(BaseModel):
    origin_latitude: float = Field(ge=-90, le=90)
    origin_longitude: float = Field(ge=-180, le=180)
    destination_latitude: float = Field(ge=-90, le=90)
    destination_longitude: float = Field(ge=-180, le=180)
    travel_mode: str = Field(default="DRIVE", pattern="^(DRIVE|TWO_WHEELER|BICYCLE|WALK)$")
    routing_preference: str = Field(default="TRAFFIC_AWARE", pattern="^(TRAFFIC_UNAWARE|TRAFFIC_AWARE|TRAFFIC_AWARE_OPTIMAL)$")
    compute_alternative_routes: bool = True
