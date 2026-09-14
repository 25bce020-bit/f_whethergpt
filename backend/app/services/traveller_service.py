"""Deterministic, weather-grounded travel and outdoor planning guidance."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


# WeatherGPT application heuristics, not official IMD thresholds.
TRAVEL_RAIN_PROBABILITY_CAUTION = 60
TRAVEL_HEAVY_RAIN_MM = 25
TRAVEL_STRONG_WIND_KMH = 35
TRAVEL_THUNDERSTORM_CODES = {95, 96, 99}


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def select_travel_forecast(forecast: list[dict], time_hint: str | None) -> dict | None:
    if not forecast:
        return None
    offsets = {"tomorrow": 1, "day_after_tomorrow": 2}
    if time_hint in offsets:
        target = (date.today() + timedelta(days=offsets[time_hint])).isoformat()
        return next((item for item in forecast if item.get("date") == target), None)
    return forecast[0]


def _warning_actions(warnings: list[dict]) -> list[dict[str, Any]]:
    actions = []
    for warning in warnings:
        official = {key: warning.get(key) for key in ("event", "severity", "headline")}
        text = " ".join(str(warning.get(key) or "") for key in ("event", "headline", "description")).lower()
        if any(word in text for word in ("thunder", "lightning", "storm", "heavy rain", "flood", "cyclone", "wind", "gust")):
            advice = "Outdoor activities may be risky during the warning period. Check official local updates before travelling."
        else:
            advice = "Review the official warning details and check official local updates before travelling."
        actions.append({"official_imd_warning": official, "weathergpt_traveller_advice": advice})
    return actions


def _hour_window(hours: list[dict]) -> dict[str, str] | None:
    scored: list[tuple[int, str, str]] = []
    for label, start, end in (("morning", 6, 11), ("afternoon", 12, 17), ("evening", 18, 23)):
        period = [hour for hour in hours if len(str(hour.get("time", ""))) >= 13 and start <= int(str(hour["time"])[11:13]) <= end]
        if not period:
            continue
        risk = 0
        for hour in period:
            probability, rain, wind = _number(hour.get("rain_probability_percent")), _number(hour.get("precipitation_mm")), _number(hour.get("wind_speed_kmh"))
            risk += 3 if hour.get("weather_code") in TRAVEL_THUNDERSTORM_CODES else 0
            risk += 2 if rain is not None and rain >= TRAVEL_HEAVY_RAIN_MM else 0
            risk += 1 if probability is not None and probability >= TRAVEL_RAIN_PROBABILITY_CAUTION else 0
            risk += 1 if wind is not None and wind >= TRAVEL_STRONG_WIND_KMH else 0
        scored.append((risk, label, "Lowest weather-risk period in the supplied hourly forecast."))
    if not scored:
        return None
    _, period, reason = min(scored)
    return {"period": period, "reason": reason}


def build_traveller_advisory(
    *, destination: str | None, current_weather: dict | None, forecast: list[dict] | None,
    hourly_forecast: list[dict] | None, imd_warnings: list[dict] | None,
    time_hint: str | None = None,
) -> dict[str, Any]:
    """Convert existing weather and IMD data into a travel advisory without fetching data."""
    day = select_travel_forecast(forecast or [], time_hint)
    hours = hourly_forecast or []
    warnings_available = imd_warnings is not None
    warning_actions = _warning_actions(imd_warnings or [])
    values = [day] if day else []
    values.extend(hours)
    has_weather = bool(day or current_weather or hours)
    rain_probability = max((value for value in (_number(hour.get("rain_probability_percent")) for hour in hours) if value is not None), default=None)
    rainfall = max((value for value in (_number(item.get("precipitation_mm")) for item in values) if value is not None), default=None)
    wind = max((value for value in (_number(item.get("wind_speed_kmh") or item.get("wind_speed_max_kmh")) for item in values) if value is not None), default=None)
    thunderstorm = any(item.get("weather_code") in TRAVEL_THUNDERSTORM_CODES for item in values)

    reasons: list[str] = []
    if not has_weather:
        status = "UNAVAILABLE"
        reasons.append("Travel suitability cannot be assessed because weather data were unavailable.")
    elif warning_actions or thunderstorm or (rainfall is not None and rainfall >= TRAVEL_HEAVY_RAIN_MM):
        status = "UNFAVORABLE"
        if warning_actions:
            reasons.append("An official IMD warning was supplied for this location.")
        if thunderstorm:
            reasons.append("Thunderstorm conditions are present in the supplied forecast.")
        if rainfall is not None and rainfall >= TRAVEL_HEAVY_RAIN_MM:
            reasons.append("Heavy precipitation is present in the supplied forecast.")
    elif (rain_probability is not None and rain_probability >= TRAVEL_RAIN_PROBABILITY_CAUTION) or (wind is not None and wind >= TRAVEL_STRONG_WIND_KMH):
        status = "CAUTION"
        if rain_probability is not None and rain_probability >= TRAVEL_RAIN_PROBABILITY_CAUTION:
            reasons.append("Rain probability is elevated in the supplied hourly forecast.")
        if wind is not None and wind >= TRAVEL_STRONG_WIND_KMH:
            reasons.append("Strong wind is present in the supplied forecast.")
    else:
        status = "GOOD"
        reasons.append("No heavy rain, thunderstorm, strong-wind, or supplied official-warning signal was found in the available weather data.")

    packing: list[str] = []
    temperature = _number((day or {}).get("temperature_max_c"))
    if rainfall is not None and rainfall > 0 or (rain_probability is not None and rain_probability >= TRAVEL_RAIN_PROBABILITY_CAUTION):
        packing.append("Carry an umbrella or rain jacket.")
    if temperature is not None and temperature >= 32:
        packing.extend(["Carry water.", "Use light clothing and sun protection."])
    if temperature is not None and temperature <= 15:
        packing.append("Carry warm clothing.")
    if wind is not None and wind >= TRAVEL_STRONG_WIND_KMH:
        packing.append("Use caution for exposed outdoor activities in strong wind.")
    if not packing and has_weather:
        packing.append("Pack for the supplied forecast conditions and check updates before departure.")
    if not packing:
        packing.append("Packing advice cannot be tailored until weather data are available.")

    return {
        "mode": "traveller", "destination": destination, "travel_time": time_hint or "unspecified",
        "travel_suitability": {"status": status, "reasons": reasons},
        "packing": packing,
        "outdoor_activity": {"status": status, "reason": reasons[0]},
        "best_window": _hour_window(hours),
        "hourly_data_status": "available" if hours else "unavailable",
        "imd_warning_status": "available" if warnings_available else "unavailable",
        "imd_actions": warning_actions,
        "limitations": ["Travel suitability is a WeatherGPT weather heuristic, not an official travel restriction.", "Road, traffic, booking, and attraction conditions are not available."],
    }


def format_traveller_advisory(advisory: dict[str, Any]) -> str:
    suitability = advisory["travel_suitability"]
    lines = [f"Traveller Advisory: {suitability['status']}", *suitability["reasons"], "Packing: " + " ".join(advisory["packing"])]
    if advisory.get("best_window"):
        lines.append(f"Best weather window: {advisory['best_window']['period']}.")
    elif advisory.get("hourly_data_status") == "unavailable":
        lines.append("A best travel window is unavailable because hourly forecast data were not supplied.")
    for action in advisory["imd_actions"]:
        lines.append(f"Official IMD warning: {action['official_imd_warning'].get('event') or 'IMD weather warning'}.")
        lines.append(f"WeatherGPT traveller advice: {action['weathergpt_traveller_advice']}")
    return "\n".join(lines)
