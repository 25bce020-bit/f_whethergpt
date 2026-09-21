"""Google Routes API integration for Traveller Mode.

This service is intentionally limited to route retrieval. It does not perform
weather analysis or route-risk scoring; later Traveller sprints consume its
structured output.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


GOOGLE_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
DEFAULT_TIMEOUT_SECONDS = 15.0


class GoogleRoutesError(RuntimeError):
    """Raised when Google Routes cannot return a usable route response."""


def _parse_duration_seconds(value: Any) -> float | None:
    if not isinstance(value, str) or not value.endswith("s"):
        return None
    try:
        return float(value[:-1])
    except ValueError:
        return None


def _normalize_route(route: dict[str, Any], index: int) -> dict[str, Any]:
    distance_m = route.get("distanceMeters")
    duration_seconds = _parse_duration_seconds(route.get("duration"))
    return {
        "route_index": index,
        "distance_m": distance_m,
        "distance_km": round(distance_m / 1000, 2) if isinstance(distance_m, (int, float)) else None,
        "duration_seconds": duration_seconds,
        "duration_minutes": round(duration_seconds / 60, 1) if duration_seconds is not None else None,
        "polyline": (route.get("polyline") or {}).get("encodedPolyline"),
    }


async def compute_routes(
    *,
    origin_latitude: float,
    origin_longitude: float,
    destination_latitude: float,
    destination_longitude: float,
    travel_mode: str = "DRIVE",
    routing_preference: str = "TRAFFIC_AWARE",
    compute_alternative_routes: bool = True,
) -> dict[str, Any]:
    """Return Google route geometry and travel metadata.

    The API key is read only from the backend environment. No key is returned
    in the response and no weather/risk interpretation is performed here.
    """

    api_key = os.getenv("GOOGLE_ROUTES_API_KEY")
    if not api_key:
        raise GoogleRoutesError("Google Routes API is not configured.")

    body = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin_latitude,
                    "longitude": origin_longitude,
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination_latitude,
                    "longitude": destination_longitude,
                }
            }
        },
        "travelMode": travel_mode,
        "routingPreference": routing_preference,
        "computeAlternativeRoutes": compute_alternative_routes,
        "languageCode": "en-US",
        "units": "METRIC",
    }

    field_mask = (
        "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline"
    )
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.post(GOOGLE_ROUTES_URL, json=body, headers=headers)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise GoogleRoutesError(
            f"Google Routes request failed with status {exc.response.status_code}."
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise GoogleRoutesError("Google Routes service is temporarily unavailable.") from exc

    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes:
        raise GoogleRoutesError("Google Routes returned no routes.")

    normalized = [_normalize_route(route, index) for index, route in enumerate(routes)]
    return {
        "provider": "Google Routes API",
        "travel_mode": travel_mode,
        "routing_preference": routing_preference,
        "routes": normalized,
    }
