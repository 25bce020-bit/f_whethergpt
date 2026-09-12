def generate_weather_advisories(
    temperature_c: float,
    rain_probability_percent: float,
    wind_speed_kmh: float,
    precipitation_mm: float = 0,
    weather_code: int | None = None,
    humidity_percent: float = 0,
) -> list[dict]:

    advisories = []

    # --------------------------------------------------
    # RAIN
    # --------------------------------------------------

    if rain_probability_percent >= 80:
        advisories.append({
            "type": "RAIN",
            "severity": "HIGH",
            "message": (
                "High chance of rain. Carry an umbrella and "
                "be cautious during outdoor activities."
            ),
            "evidence": {
                "rain_probability_percent": rain_probability_percent
            }
        })

    elif rain_probability_percent >= 40:
        advisories.append({
            "type": "RAIN",
            "severity": "MODERATE",
            "message": (
                "There is a moderate chance of rain. "
                "Consider carrying an umbrella."
            ),
            "evidence": {
                "rain_probability_percent": rain_probability_percent
            }
        })

    # --------------------------------------------------
    # HEAVY PRECIPITATION
    # --------------------------------------------------

    if precipitation_mm >= 10:
        advisories.append({
            "type": "HEAVY_RAIN",
            "severity": "HIGH",
            "message": (
                "Heavy precipitation is expected. "
                "There may be localized waterlogging or reduced visibility."
            ),
            "evidence": {
                "precipitation_mm": precipitation_mm
            }
        })

    # --------------------------------------------------
    # THUNDERSTORM
    # --------------------------------------------------

    # WMO weather codes 95-99 represent thunderstorm conditions
    if weather_code is not None and weather_code >= 95:
        advisories.append({
            "type": "THUNDERSTORM",
            "severity": "HIGH",
            "message": (
                "Thunderstorm conditions are possible. "
                "Avoid exposed outdoor areas and seek shelter if thunder is nearby."
            ),
            "evidence": {
                "weather_code": weather_code
            }
        })

    # --------------------------------------------------
    # HEAT
    # --------------------------------------------------

    if temperature_c >= 40:
        advisories.append({
            "type": "HEAT",
            "severity": "HIGH",
            "message": (
                "Extreme heat conditions are expected. "
                "Stay hydrated and avoid prolonged outdoor exposure."
            ),
            "evidence": {
                "temperature_c": temperature_c
            }
        })

    elif temperature_c >= 35:
        advisories.append({
            "type": "HEAT",
            "severity": "MODERATE",
            "message": (
                "High temperature is expected. "
                "Stay hydrated and limit prolonged exposure to the afternoon heat."
            ),
            "evidence": {
                "temperature_c": temperature_c
            }
        })

    # --------------------------------------------------
    # STRONG WIND
    # --------------------------------------------------

    if wind_speed_kmh >= 50:
        advisories.append({
            "type": "WIND",
            "severity": "HIGH",
            "message": (
                "Strong winds are possible. Take care around "
                "trees, temporary structures, and exposed areas."
            ),
            "evidence": {
                "wind_speed_kmh": wind_speed_kmh
            }
        })

    # --------------------------------------------------
    # HIGH HUMIDITY
    # --------------------------------------------------

    if humidity_percent >= 80 and temperature_c >= 30:
        advisories.append({
            "type": "HUMIDITY",
            "severity": "MODERATE",
            "message": (
                "High humidity may make conditions feel hotter "
                "and increase discomfort. Stay hydrated."
            ),
            "evidence": {
                "humidity_percent": humidity_percent,
                "temperature_c": temperature_c
            }
        })

    return advisories