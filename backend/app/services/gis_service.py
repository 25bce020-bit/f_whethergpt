"""Deterministic transformations from existing WeatherGPT data to map payloads."""

from __future__ import annotations

from math import isfinite
from typing import Any

from app.schemas.gis import GeographicPoint, MapBounds


def validate_coordinates(latitude: float, longitude: float) -> tuple[float, float]:
    """Validate coordinates without clamping or swapping values."""
    try:
        latitude, longitude = float(latitude), float(longitude)
    except (TypeError, ValueError) as exc:
        raise ValueError("Latitude and longitude must be numeric.") from exc
    if not isfinite(latitude) or not isfinite(longitude):
        raise ValueError("Latitude and longitude must be finite numbers.")
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")
    return latitude, longitude


def validate_bounds(north: float, south: float, east: float, west: float) -> MapBounds:
    """Return a validated, JSON-ready viewport bounds model."""
    return MapBounds(north=north, south=south, east=east, west=west)


def geographic_point(location: dict[str, Any] | None = None, *, latitude: float | None = None, longitude: float | None = None) -> GeographicPoint:
    """Normalize an existing geocoder result or already validated coordinates."""
    source = location or {}
    latitude = source.get("latitude") if latitude is None else latitude
    longitude = source.get("longitude") if longitude is None else longitude
    latitude, longitude = validate_coordinates(latitude, longitude)
    return GeographicPoint(
        latitude=latitude,
        longitude=longitude,
        name=source.get("name"),
        country=source.get("country"),
        state=source.get("admin1") or source.get("state"),
    )


def point_payload(point: GeographicPoint) -> dict[str, Any]:
    return point.model_dump()


def map_marker(point: GeographicPoint, weather: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a stable marker with only weather fields already supplied."""
    marker = {
        "id": f"{point.latitude:.4f}:{point.longitude:.4f}",
        "latitude": point.latitude,
        "longitude": point.longitude,
        "title": point.name or "Weather location",
    }
    if weather is not None:
        marker["weather"] = weather
    return marker


def geojson_feature(point: GeographicPoint, properties: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a Point feature; GeoJSON always uses longitude, latitude order."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [point.longitude, point.latitude]},
        "properties": {"name": point.name, **(properties or {})},
    }


def current_weather_map(point: GeographicPoint, weather: dict[str, Any]) -> dict[str, Any]:
    return {
        "location": point_payload(point),
        "weather": weather,
        "map": {"latitude": point.latitude, "longitude": point.longitude},
        "marker": map_marker(point, weather),
        "geojson": geojson_feature(point, {"weather_code": weather.get("weather_code"), "temperature_c": weather.get("temperature_c")}),
    }


def forecast_map(point: GeographicPoint, forecast: list[dict[str, Any]]) -> dict[str, Any]:
    return {"location": point_payload(point), "forecast": forecast, "map": {"latitude": point.latitude, "longitude": point.longitude}}


def hourly_map(point: GeographicPoint, hourly: list[dict[str, Any]]) -> dict[str, Any]:
    return {"location": point_payload(point), "hourly": hourly, "map": {"latitude": point.latitude, "longitude": point.longitude}}


def warning_map_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Expose only explicit CAP circle centres; never infer a point from alert text."""
    point = None
    for area in alert.get("areas", []):
        circles = area.get("circles", [])
        if circles:
            circle = circles[0]
            try:
                point = geographic_point(latitude=circle["latitude"], longitude=circle["longitude"])
            except (KeyError, TypeError, ValueError):
                point = None
            break
    return {
        "id": alert.get("identifier"),
        "title": alert.get("headline") or alert.get("event"),
        "event": alert.get("event"),
        "severity": alert.get("severity"),
        "sent_at": alert.get("sent"),
        "source": "IMD",
        "official": bool(alert.get("official", True)),
        "coordinates_available": point is not None,
        "location": point_payload(point) if point else None,
    }
