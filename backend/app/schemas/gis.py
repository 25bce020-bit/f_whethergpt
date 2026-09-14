"""Pydantic models for the lightweight GIS/map API."""

from math import isfinite
from pydantic import BaseModel, Field, field_validator, model_validator


class GeographicPoint(BaseModel):
    latitude: float
    longitude: float
    name: str | None = None
    country: str | None = None
    state: str | None = None

    @field_validator("latitude", "longitude")
    @classmethod
    def coordinates_must_be_finite(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("Coordinates must be finite numbers.")
        return value

    @model_validator(mode="after")
    def coordinates_must_be_in_range(self):
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180.")
        return self


class MapBounds(BaseModel):
    north: float = Field(ge=-90, le=90)
    south: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)
    west: float = Field(ge=-180, le=180)

    @field_validator("north", "south", "east", "west")
    @classmethod
    def bounds_must_be_finite(cls, value: float) -> float:
        if not isfinite(value):
            raise ValueError("Bounds must be finite numbers.")
        return value

    @model_validator(mode="after")
    def north_must_not_be_below_south(self):
        if self.north < self.south:
            raise ValueError("north must be greater than or equal to south.")
        return self
