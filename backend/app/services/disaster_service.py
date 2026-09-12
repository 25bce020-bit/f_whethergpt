def _safe_number(value, default=0):
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def generate_disaster_alerts(forecast):
    """
    Analyze daily weather forecast data and generate
    extreme-weather risk alerts.

    This is a preliminary risk engine.
    Official meteorological warnings will be integrated
    later as an authoritative alert source.
    """

    alerts = []

    for day in forecast:

        date = day.get("date")

        condition = str(
            day.get("condition", "")
        ).lower()

        temperature_max = _safe_number(
            day.get("temperature_max_c")
        )

        temperature_min = _safe_number(
            day.get("temperature_min_c")
        )

        precipitation = _safe_number(
            day.get("precipitation_mm")
        )

        wind_speed = _safe_number(
            day.get("wind_speed_max_kmh")
        )

        # ----------------------------------------------------
        # Extreme heat
        # ----------------------------------------------------

        if temperature_max >= 45:

            alerts.append({
                "date": date,
                "type": "extreme_heat",
                "severity": "severe",
                "title": "Extreme Heat Risk",
                "message": (
                    f"Extreme heat is possible on {date}. "
                    "Avoid prolonged outdoor exposure, stay hydrated, "
                    "and follow local heat warnings."
                ),
            })

        elif temperature_max >= 40:

            alerts.append({
                "date": date,
                "type": "heat",
                "severity": "high",
                "title": "High Heat Risk",
                "message": (
                    f"Very high temperatures are expected on {date}. "
                    "Take precautions against heat exposure."
                ),
            })

        # ----------------------------------------------------
        # Heavy precipitation / flood risk
        # ----------------------------------------------------

        if precipitation >= 50:

            alerts.append({
                "date": date,
                "type": "heavy_rain",
                "severity": "severe",
                "title": "Heavy Rainfall Risk",
                "message": (
                    f"Very heavy precipitation is possible on {date}. "
                    "Localized flooding and travel disruption may occur. "
                    "Follow local authorities' warnings."
                ),
            })

        elif precipitation >= 25:

            alerts.append({
                "date": date,
                "type": "heavy_rain",
                "severity": "high",
                "title": "Heavy Rainfall",
                "message": (
                    f"Heavy rainfall is possible on {date}. "
                    "Be alert for waterlogging and localized flooding."
                ),
            })

        # ----------------------------------------------------
        # Strong winds
        # ----------------------------------------------------

        if wind_speed >= 60:

            alerts.append({
                "date": date,
                "type": "strong_wind",
                "severity": "severe",
                "title": "Severe Wind Risk",
                "message": (
                    f"Severe winds are possible on {date}. "
                    "Avoid exposed areas and secure loose objects."
                ),
            })

        elif wind_speed >= 40:

            alerts.append({
                "date": date,
                "type": "strong_wind",
                "severity": "high",
                "title": "Strong Wind",
                "message": (
                    f"Strong winds are possible on {date}. "
                    "Exercise caution during outdoor activities."
                ),
            })

        # ----------------------------------------------------
        # Thunderstorm
        # ----------------------------------------------------

        if "thunderstorm" in condition:

            alerts.append({
                "date": date,
                "type": "thunderstorm",
                "severity": "high",
                "title": "Thunderstorm Risk",
                "message": (
                    f"Thunderstorm conditions are possible on {date}. "
                    "Avoid exposed outdoor areas and seek shelter "
                    "if thunderstorms develop."
                ),
            })

        # ----------------------------------------------------
        # Combined heavy rain + strong wind
        # ----------------------------------------------------

        if (
            precipitation >= 25
            and wind_speed >= 40
        ):

            alerts.append({
                "date": date,
                "type": "severe_weather",
                "severity": "severe",
                "title": "Severe Weather Risk",
                "message": (
                    f"Heavy precipitation and strong winds may occur "
                    f"together on {date}. Monitor official weather "
                    "warnings and avoid unnecessary travel."
                ),
            })

        # ----------------------------------------------------
        # Cold
        # ----------------------------------------------------

        if temperature_min <= 5:

            alerts.append({
                "date": date,
                "type": "extreme_cold",
                "severity": "high",
                "title": "Cold Weather Risk",
                "message": (
                    f"Very low temperatures are possible on {date}. "
                    "Take appropriate precautions against cold exposure."
                ),
            })

    return alerts