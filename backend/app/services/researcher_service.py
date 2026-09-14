"""Structured, source-aware analysis for Researcher Mode.

This service only interprets data already retrieved by WeatherGPT's existing
services. It deliberately makes no claims about significance, climate change, or
measurements that are absent from its input.
"""

from __future__ import annotations

import re
from typing import Any


def choose_researcher_tool(message: str) -> str | None:
    """Conservative routing fallback when LLM tool selection is unavailable."""
    text = message.lower()
    has_model_signal = bool(re.search(r"\b(gfs|nwp|model|open-meteo)\b", text))
    if has_model_signal and re.search(r"\b(compare|comparison|agree|agreement|disagree|disagreement|confidence)\b", text):
        return "model_comparison"
    if re.search(r"\b(gfs|nwp|numerical weather|forecast model|model output)\b", text):
        return "nwp_gfs"
    if re.search(r"\b(historical|history|recent weather|last few days|last week|yesterday)\b", text):
        return "historical_weather"
    if re.search(r"\b(climate|trend|pattern)\b", text):
        return "climate"
    if re.search(r"\b(imd|official warning|government warning|official alert)\b", text):
        return "official_warning"
    if re.search(r"\b(extreme weather|weather event|heavy rainfall risk|severe weather|flood risk|thunderstorm risk)\b", text):
        return "disaster_alert"
    return None


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _daily_summary(entries: list[dict]) -> dict[str, Any]:
    temperatures = []
    precipitation = []
    for item in entries:
        high, low = _number(item.get("temperature_max_c")), _number(item.get("temperature_min_c"))
        if high is not None and low is not None:
            temperatures.append((high + low) / 2)
        rain = _number(item.get("precipitation_mm"))
        if rain is not None:
            precipitation.append(rain)

    summary: dict[str, Any] = {"available_entries": len(entries)}
    if temperatures:
        summary["mean_daily_temperature_c"] = round(sum(temperatures) / len(temperatures), 2)
        summary["minimum_daily_mean_temperature_c"] = round(min(temperatures), 2)
        summary["maximum_daily_mean_temperature_c"] = round(max(temperatures), 2)
    if precipitation:
        summary["total_precipitation_mm"] = round(sum(precipitation), 2)
        summary["rainy_entries"] = sum(value > 0 for value in precipitation)
    if len(temperatures) >= 2:
        change = temperatures[-1] - temperatures[0]
        summary["observed_temperature_direction"] = (
            "increasing" if change > 0.5 else "decreasing" if change < -0.5 else "little change"
        )
    return summary


def _sources_for(data: dict) -> list[str]:
    sources = []
    if any(key in data for key in ("weather", "forecast", "hourly_forecast", "historical_weather", "climate_data")):
        sources.append("Open-Meteo")
    if any(key in data for key in ("nwp", "nwp_model", "daily", "hourly")) and (
        data.get("model") == "NCEP GFS" or data.get("nwp_model") or data.get("nwp")
    ):
        sources.append("NCEP GFS")
    if data.get("warnings") is not None or data.get("official_warnings") is not None:
        sources.append("IMD official warning")
    if any(key in data for key in ("alerts", "advisories", "comparison", "model_comparison")):
        sources.append("WeatherGPT-derived analysis")
    return sources


def build_researcher_analysis(data: dict, tool: str | None = None) -> dict[str, Any]:
    """Build a JSON-serializable research summary from existing structured data."""
    observations: dict[str, Any] = {}
    interpretation: list[str] = []
    limitations: list[str] = []

    historical = data.get("historical_weather") or data.get("climate_data")
    if historical is not None:
        observations["historical_summary"] = _daily_summary(historical)
        observations["period_entries"] = historical
        interpretation.append("This summary describes only the retrieved observation period.")
        limitations.append("The available recent observations do not establish a long-term climate trend.")

    forecast = data.get("forecast")
    if forecast is not None:
        observations["forecast_summary"] = _daily_summary(forecast)
        observations["forecast_entries"] = forecast
        interpretation.append("Forecast values are model-derived estimates, not observed weather.")

    if data.get("weather") is not None:
        observations["current_weather"] = data["weather"]
        interpretation.append("Current conditions are retrieved observations at the reported time.")

    if data.get("hourly_forecast") is not None:
        observations["hourly_forecast"] = data["hourly_forecast"]
        interpretation.append("Hourly values are forecast output for the requested period.")

    if data.get("daily") is not None or data.get("hourly") is not None:
        observations["gfs_model"] = {
            "model": data.get("model", "NCEP GFS"),
            "provider": data.get("provider"),
            "daily": data.get("daily", []),
            "hourly": data.get("hourly", []),
        }
        interpretation.append("GFS values are numerical weather prediction output, not direct observations.")
        limitations.append("Model output does not guarantee the observed weather will match the forecast.")

    comparison = data.get("comparison")
    if comparison is None and isinstance(data.get("model_comparison"), dict):
        comparison = data["model_comparison"].get("comparison")
    if comparison is not None:
        observations["model_comparison"] = comparison
        confidence = [item.get("confidence") for item in comparison if item.get("confidence")]
        if confidence:
            observations["comparison_confidence"] = confidence
        interpretation.append("Model agreement is an existing WeatherGPT comparison result and is not certainty.")

    warnings = data.get("warnings", data.get("official_warnings"))
    if warnings is not None:
        observations["official_imd_warnings"] = warnings
        if warnings:
            interpretation.append("The listed warning information is official IMD source content; interpretation is separate.")
        else:
            interpretation.append("No matching official IMD warning was supplied for this location.")

    if data.get("alerts") is not None:
        observations["weathergpt_derived_risks"] = data["alerts"]
        interpretation.append("These risks are WeatherGPT-derived from available forecast thresholds, not official warnings.")

    if not observations:
        limitations.append("No structured weather data were available for analysis.")

    return {
        "mode": "researcher",
        "tool": tool,
        "location": data.get("location"),
        "sources": _sources_for(data),
        "observations": observations,
        "interpretation": interpretation,
        "limitations": limitations,
    }


def format_researcher_analysis(analysis: dict[str, Any]) -> str:
    """Safe fallback if the existing LLM response call is unavailable."""
    lines = ["Research Summary"]
    location = analysis.get("location") or {}
    if location.get("name"):
        lines.append(f"Location: {location['name']}")
    sources = analysis.get("sources", [])
    if sources:
        lines.append("Sources: " + ", ".join(sources))
    summary = analysis.get("observations", {}).get("historical_summary") or analysis.get("observations", {}).get("forecast_summary")
    if summary:
        lines.append("Observed/retrieved summary: " + ", ".join(f"{key}={value}" for key, value in summary.items()))
    lines.extend("Interpretation: " + item for item in analysis.get("interpretation", []))
    lines.extend("Limitation: " + item for item in analysis.get("limitations", []))
    return "\n".join(lines)
