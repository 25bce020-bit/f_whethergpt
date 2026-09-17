"""Deterministic, weather-grounded farming guidance for Farmer Mode.

This module deliberately does not estimate soil moisture, crop maturity, disease,
or pesticide efficacy.  It converts only supplied forecast/current/IMD data into
conservative operational guidance.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any


SUPPORTED_CROPS = ("wheat", "rice", "paddy", "cotton", "tomato", "maize", "soybean", "sugarcane")
GROWTH_STAGES = ("sowing", "germination", "vegetative", "flowering", "fruiting/grain filling", "maturity", "harvesting")

# Central, operational thresholds. They intentionally match the project's existing
# recommendation/advisory conventions rather than claiming crop-science precision.
RAIN_PROBABILITY_CAUTION = 60
PRECIPITATION_CAUTION_MM = 2
SPRAY_WIND_CAUTION_KMH = 25
SEVERE_WIND_KMH = 40
HEAVY_RAIN_MM = 25
THUNDERSTORM_CODES = {95, 96, 99}


def extract_farmer_context(message: str) -> dict[str, str | None]:
    """Extract only explicit supported crop and simple growth-stage statements."""
    text = message.lower()
    crop = next((item for item in SUPPORTED_CROPS if re.search(rf"\b{re.escape(item)}\b", text)), None)
    if crop == "paddy":
        crop = "rice"

    stage = None
    if re.search(r"\b(fruiting|grain filling)\b", text):
        stage = "fruiting/grain filling"
    else:
        stage = next((item for item in GROWTH_STAGES if re.search(rf"\b{re.escape(item)}\b", text)), None)
    return {"crop": crop, "growth_stage": stage}


def is_farmer_context_statement(
    message: str,
    extracted: dict[str, str | None],
) -> bool:
    """Identify simple crop/stage updates that need no weather lookup."""

    # There must be explicit farmer crop/stage information.
    if not (
        extracted.get("crop")
        or extracted.get("growth_stage")
    ):
        return False

    text = message.lower().strip()

    # An explicit question is never just context.
    if "?" in text:
        return False

    # These phrases indicate that the farmer is asking for advice,
    # a decision, a forecast, or a weather-based recommendation.
    advisory_patterns = [
        r"\bshould\s+(?:i|we|he|she|they)\b",
        r"\bwould\s+(?:it|this|that)\b",
        r"\bcan\s+(?:i|we|it)\b",
        r"\bcould\s+(?:i|we|it)\b",
        r"\bmay\s+(?:i|we|it)\b",
        r"\bis\s+(?:it|this|that)\b",
        r"\bare\s+(?:there|we|the)\b",
        r"\bwhen\s+should\b",
        r"\bwhat\s+should\b",
        r"\bhow\s+should\b",
        r"\bwhich\s+(?:day|time|window)\b",
        r"\brecommend(?:ed|ation)?\b",
        r"\badvis(?:e|able|ory|ability)\b",
        r"\bsuitable\b",
        r"\bgood\s+(?:time|day|window)\b",
        r"\bbest\s+(?:time|day|window)\b",
        r"\bweather\s+(?:for|condition|conditions|forecast)\b",
        r"\bforecast\s+(?:for|tomorrow|today|this|next)\b",
        r"\birrigat(?:e|ion)\b",
        r"\bspray(?:ing)?\s+(?:tomorrow|today|now|this|next)\b",
        r"\bsow(?:ing)?\s+(?:tomorrow|today|now|this|next)\b",
        r"\bharvest(?:ing)?\s+(?:tomorrow|today|now|this|next)\b",
    ]

    for pattern in advisory_patterns:
        if re.search(pattern, text):
            return False

    # No question/advisory pattern was found, so treat the message
    # as a simple farmer context update.
    return True

def select_farmer_forecast(forecast: list[dict], time_hint: str | None) -> list[dict]:
    if not forecast:
        return []
    if time_hint == "tomorrow":
        target = (date.today() + timedelta(days=1)).isoformat()
        return [item for item in forecast if item.get("date") == target] or forecast[1:2]
    if time_hint in {"next_3_days", "next_few_days", "next_week"}:
        limits = {"next_3_days": 3, "next_few_days": 5, "next_week": 7}
        return forecast[:limits[time_hint]]
    return forecast[:1]


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _has_rain_risk(day: dict | None, hours: list[dict]) -> bool | None:
    values_present = False
    if day:
        precipitation = _number(day.get("precipitation_mm"))
        if precipitation is not None:
            values_present = True
            if precipitation >= PRECIPITATION_CAUTION_MM:
                return True
        if day.get("weather_code") in THUNDERSTORM_CODES or "rain" in str(day.get("condition", "")).lower():
            return True
    for hour in hours:
        probability = _number(hour.get("rain_probability_percent"))
        precipitation = _number(hour.get("precipitation_mm"))
        if probability is not None or precipitation is not None:
            values_present = True
        if (probability is not None and probability >= RAIN_PROBABILITY_CAUTION) or (
            precipitation is not None and precipitation >= PRECIPITATION_CAUTION_MM
        ) or hour.get("weather_code") in THUNDERSTORM_CODES:
            return True
    return False if values_present else None


def _max_wind(day: dict | None, hours: list[dict]) -> float | None:
    values = [_number((day or {}).get("wind_speed_max_kmh"))]
    values.extend(_number(hour.get("wind_speed_kmh")) for hour in hours)
    values = [value for value in values if value is not None]
    return max(values) if values else None


def _has_thunderstorm(day: dict | None, hours: list[dict]) -> bool:
    return bool(
        (day or {}).get("weather_code") in THUNDERSTORM_CODES
        or any(hour.get("weather_code") in THUNDERSTORM_CODES for hour in hours)
    )


def _recommendation(text: str, reason: str, confidence: str) -> dict[str, str]:
    return {"recommendation": text, "reason": reason, "confidence": confidence}


def imd_farmer_actions(warnings: list[dict]) -> list[dict[str, str]]:
    actions = []
    for warning in warnings:
        official = {
            "event": str(warning.get("event") or "IMD weather warning"),
            "severity": str(warning.get("severity") or "Not specified"),
            "headline": str(warning.get("headline") or ""),
        }
        text = " ".join(str(warning.get(key) or "") for key in ("event", "headline", "description")).lower()
        if any(word in text for word in ("heavy rain", "rainfall", "flood", "precipitation")):
            action = "Consider protecting harvested produce, checking field drainage, and avoiding non-essential field operations during severe weather."
        elif any(word in text for word in ("wind", "gust", "cyclone")):
            action = "Avoid spraying during strong winds and secure vulnerable farm materials where appropriate."
        elif any(word in text for word in ("thunder", "lightning", "storm")):
            action = "Avoid exposed field activity while thunderstorm conditions are present and follow local safety guidance."
        elif any(word in text for word in ("heat", "hot")):
            action = "Plan strenuous field work for cooler periods and ensure people have drinking water and shade where possible."
        else:
            action = "Review the official warning details and avoid field operations that could be unsafe during the warned conditions."
        actions.append({"official_imd_warning": official, "weathergpt_farmer_advisory": action})
    return actions


def build_farmer_advisory(
    *,
    crop: str | None,
    growth_stage: str | None,
    current_weather: dict | None,
    forecast: list[dict] | None,
    hourly_forecast: list[dict] | None,
    imd_warnings: list[dict] | None,
    time_hint: str | None = None,
    agromet_advisory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return structured decisions based only on data supplied by the caller."""
    forecast = forecast or []
    hours = hourly_forecast or []
    selected_days = select_farmer_forecast(forecast, time_hint)
    day = selected_days[0] if selected_days else None
    rain_risk = _has_rain_risk(day, hours)
    wind = _max_wind(day, hours)
    thunderstorm = _has_thunderstorm(day, hours)

    weather_summary: dict[str, Any] = {}
    if current_weather:
        for key in ("time", "temperature_c", "precipitation_mm", "wind_speed_kmh", "condition"):
            if current_weather.get(key) is not None:
                weather_summary[f"current_{key}"] = current_weather[key]
    if day:
        weather_summary["forecast_day"] = day
    if not weather_summary:
        weather_summary["availability"] = "Current and forecast weather data were unavailable."

    if rain_risk is None:
        irrigation = _recommendation("Irrigation suitability cannot be assessed from the available weather data.", "No usable rain or precipitation forecast was supplied.", "low")
        spraying = _recommendation("Spraying suitability cannot be assessed from the available weather data.", "No usable rain or wind forecast was supplied.", "low")
        sowing = _recommendation("Sowing suitability cannot be assessed from the available weather data.", "No usable forecast was supplied.", "low")
        harvesting = _recommendation("Harvesting suitability cannot be assessed from the available weather data.", "No usable forecast was supplied.", "low")
    else:
        rain_reason = "Rain or a high rain chance is present in the supplied forecast." if rain_risk else "No significant rain signal is present in the supplied forecast."
        irrigation = _recommendation(
            "Irrigation may be unnecessary if the field already has adequate soil moisture." if rain_risk else "Irrigation may be considered if the field needs water.",
            rain_reason + " WeatherGPT does not have field soil-moisture data.", "medium",
        )
        unsuitable_spray = rain_risk or thunderstorm or (wind is not None and wind >= SPRAY_WIND_CAUTION_KMH)
        spray_reason = "Rain, thunderstorm, or wind conditions could interfere with application." if unsuitable_spray else "No rain, thunderstorm, or strong-wind signal is present in the supplied forecast."
        spraying = _recommendation("Delay spraying until a drier, calmer forecast window." if unsuitable_spray else "Weather conditions appear more suitable for spraying, subject to label directions and local advice.", spray_reason, "medium")
        sowing = _recommendation("Consider waiting for a more stable, less wet weather window." if rain_risk or thunderstorm else "Weather conditions appear generally suitable for sowing; this is weather-based guidance, not a crop-calendar recommendation.", rain_reason, "medium")
        harvest_risk = rain_risk or thunderstorm or (wind is not None and wind >= SEVERE_WIND_KMH)
        harvesting = _recommendation("Avoid harvesting during the wetter or stormier period if practical; protect already harvested produce." if harvest_risk else "Weather conditions appear generally more suitable for harvesting. Crop maturity cannot be determined from weather data.", "Rain, thunderstorm, or strong wind can interfere with harvest operations." if harvest_risk else "No significant wet, storm, or severe-wind signal is present in the supplied forecast.", "medium")

    today_advisory: list[str] = []
    if current_weather:
        today_advisory.append("Use the supplied current conditions when planning field work today.")
    if rain_risk:
        today_advisory.append("Keep field operations flexible because rain may affect access and application work.")
    if thunderstorm:
        today_advisory.append("Avoid exposed field activity if thunderstorms develop.")
    if wind is not None and wind >= SPRAY_WIND_CAUTION_KMH:
        today_advisory.append("Avoid spraying during the forecast windier period.")
    if not today_advisory:
        today_advisory.append("No weather-based farmer advisory can be made until current or forecast data are available.")

    agromet_available = bool(agromet_advisory and agromet_advisory.get("available") and agromet_advisory.get("advisories"))

    return {
        "crop": crop,
        "growth_stage": growth_stage,
        "weather_summary": weather_summary,
        "irrigation": irrigation,
        "spraying": spraying,
        "sowing": sowing,
        "harvesting": harvesting,
        "today_advisory": today_advisory,
        "imd_warning_status": "available" if imd_warnings is not None else "unavailable",
        "imd_actions": imd_farmer_actions(imd_warnings or []),
        "agromet_advisory": agromet_advisory if agromet_available else None,
        "agromet_status": "available" if agromet_available else "unavailable",
        "limitations": [
            "This is weather-based guidance only; WeatherGPT does not have field soil-moisture data.",
            "Crop maturity and chemical-specific pesticide instructions are not determined by this advisory.",
        ],
    }


def format_farmer_advisory(advisory: dict[str, Any]) -> str:
    """Safe response fallback when the LLM is unavailable."""
    lines = ["Farmer Advisory"]
    if advisory.get("crop"):
        crop_stage = advisory["crop"] + (f" ({advisory['growth_stage']})" if advisory.get("growth_stage") else "")
        lines.append(f"Crop context: {crop_stage}.")
    for key, label in (("irrigation", "Irrigation"), ("spraying", "Spraying"), ("sowing", "Sowing"), ("harvesting", "Harvesting")):
        item = advisory[key]
        lines.append(f"{label}: {item['recommendation']}")
    for action in advisory.get("imd_actions", []):
        warning = action["official_imd_warning"]
        lines.append(f"Official IMD warning: {warning['event']} ({warning['severity']}).")
        lines.append(f"WeatherGPT farmer advisory: {action['weathergpt_farmer_advisory']}")
    if advisory.get("imd_warning_status") == "unavailable":
        lines.append("Official IMD warning data were unavailable for this advisory.")
    
    agromet = advisory.get("agromet_advisory")
    if agromet and agromet.get("advisories"):
        lines.append("Official IMD Agromet / GKMS Advisory:")
        for adv in agromet["advisories"]:
            crop_label = f" ({adv['crop']})" if adv.get("crop") else ""
            lines.append(f"- {adv['title']}{crop_label}: {adv['recommendation']}")
            if adv.get("valid_until"):
                lines.append(f"  Valid until: {adv['valid_until']}")
    elif advisory.get("agromet_status") == "unavailable":
        lines.append("Official IMD Agromet advisory was unavailable for this location.")
        
    return "\n".join(lines)