from typing import Any


def _safe_number(value: Any):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _difference(value1, value2):
    a = _safe_number(value1)
    b = _safe_number(value2)

    if a is None or b is None:
        return None

    return round(abs(a - b), 2)


def _compare_temperature(base, gfs):
    base_temp = _safe_number(base.get("temperature_max_c"))
    gfs_temp = _safe_number(gfs.get("temperature_max_c"))

    if base_temp is None or gfs_temp is None:
        return {
            "difference_c": None,
            "agreement": "unknown",
        }

    difference = abs(base_temp - gfs_temp)

    if difference <= 1:
        agreement = "high"
    elif difference <= 3:
        agreement = "moderate"
    else:
        agreement = "low"

    return {
        "base_model_c": base_temp,
        "gfs_c": gfs_temp,
        "difference_c": round(difference, 2),
        "agreement": agreement,
    }


def _compare_precipitation(base, gfs):
    base_rain = _safe_number(base.get("precipitation_mm"))
    gfs_rain = _safe_number(gfs.get("precipitation_mm"))

    if base_rain is None or gfs_rain is None:
        return {
            "difference_mm": None,
            "agreement": "unknown",
        }

    difference = abs(base_rain - gfs_rain)

    if difference <= 2:
        agreement = "high"
    elif difference <= 10:
        agreement = "moderate"
    else:
        agreement = "low"

    return {
        "base_model_mm": base_rain,
        "gfs_mm": gfs_rain,
        "difference_mm": round(difference, 2),
        "agreement": agreement,
    }


def _compare_wind(base, gfs):
    base_wind = _safe_number(base.get("wind_speed_max_kmh"))
    gfs_wind = _safe_number(gfs.get("wind_speed_max_kmh"))

    if base_wind is None or gfs_wind is None:
        return {
            "difference_kmh": None,
            "agreement": "unknown",
        }

    difference = abs(base_wind - gfs_wind)

    if difference <= 5:
        agreement = "high"
    elif difference <= 15:
        agreement = "moderate"
    else:
        agreement = "low"

    return {
        "base_model_kmh": base_wind,
        "gfs_kmh": gfs_wind,
        "difference_kmh": round(difference, 2),
        "agreement": agreement,
    }


def compare_daily_forecasts(base_forecast: list, gfs_forecast: list):
    gfs_by_date = {
        item.get("date"): item
        for item in gfs_forecast
        if item.get("date")
    }

    comparisons = []

    for base in base_forecast:
        forecast_date = base.get("date")

        if forecast_date not in gfs_by_date:
            continue

        gfs = gfs_by_date[forecast_date]

        temperature = _compare_temperature(base, gfs)
        precipitation = _compare_precipitation(base, gfs)
        wind = _compare_wind(base, gfs)

        agreements = [
            temperature["agreement"],
            precipitation["agreement"],
            wind["agreement"],
        ]

        known_agreements = [
            item for item in agreements
            if item != "unknown"
        ]

        if not known_agreements:
            confidence = "unknown"
        else:
            high_count = known_agreements.count("high")
            moderate_count = known_agreements.count("moderate")

            if high_count >= 2:
                confidence = "high"
            elif high_count + moderate_count >= 2:
                confidence = "moderate"
            else:
                confidence = "low"

        differences = []

        if temperature.get("difference_c") is not None:
            differences.append(
                f"temperature differs by "
                f"{temperature['difference_c']}°C"
            )

        if precipitation.get("difference_mm") is not None:
            differences.append(
                f"precipitation differs by "
                f"{precipitation['difference_mm']} mm"
            )

        if wind.get("difference_kmh") is not None:
            differences.append(
                f"wind differs by "
                f"{wind['difference_kmh']} km/h"
            )

        if confidence == "high":
            explanation = (
                "The existing forecast and NCEP GFS show "
                "strong agreement for this date."
            )
        elif confidence == "moderate":
            explanation = (
                "The models show moderate agreement, "
                "but some weather variables differ."
            )
        elif confidence == "low":
            explanation = (
                "The models show significant differences. "
                "Forecast uncertainty is relatively high."
            )
        else:
            explanation = (
                "There is insufficient data to determine "
                "model agreement."
            )

        comparisons.append({
            "date": forecast_date,
            "confidence": confidence,
            "temperature": temperature,
            "precipitation": precipitation,
            "wind": wind,
            "differences": differences,
            "explanation": explanation,
        })

    return comparisons