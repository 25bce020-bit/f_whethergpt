def safe_number(value, default=0):
    """
    Convert a value to a number safely.
    """
    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def generate_weather_recommendations(
    temperature_c=None,
    temperature_max_c=None,
    temperature_min_c=None,
    feels_like_c=None,
    rain_probability_percent=None,
    precipitation_mm=None,
    wind_speed_kmh=None,
    wind_speed_max_kmh=None,
    humidity_percent=None,
    condition=None,
    activity=None,
):
    """
    Generate practical weather-based recommendations
    using available weather data.
    """

    recommendations = []

    temperature = safe_number(
        temperature_c,
        default=safe_number(temperature_max_c)
    )

    temperature_max = safe_number(
        temperature_max_c,
        default=temperature
    )

    temperature_min = safe_number(
        temperature_min_c
    )

    feels_like = safe_number(
        feels_like_c,
        default=temperature
    )

    rain_probability = safe_number(
        rain_probability_percent
    )

    precipitation = safe_number(
        precipitation_mm
    )

    wind_speed = safe_number(
        wind_speed_kmh,
        default=safe_number(wind_speed_max_kmh)
    )

    humidity = safe_number(
        humidity_percent
    )

    condition_text = (condition or "").lower()

    # --------------------------------------------------------
    # Rain
    # --------------------------------------------------------

    rain_conditions = (
        "rain",
        "drizzle",
        "thunderstorm",
        "showers",
    )

    if (
        rain_probability >= 60
        or precipitation >= 2
        or any(word in condition_text for word in rain_conditions)
    ):
        recommendations.append(
            "Carry an umbrella or rain protection because "
            "rainy conditions are possible."
        )

    elif rain_probability >= 30:
        recommendations.append(
            "There is some chance of rain, so carrying "
            "light rain protection may be useful."
        )

    # --------------------------------------------------------
    # Extreme heat
    # --------------------------------------------------------

    if temperature_max >= 40:
        recommendations.append(
            "Very hot conditions are expected. Avoid prolonged "
            "outdoor exposure, stay hydrated, and seek shade."
        )

    elif temperature_max >= 35:
        recommendations.append(
            "Hot conditions are expected. Stay hydrated and "
            "limit prolonged exposure to direct sunlight."
        )

    elif temperature_max >= 30:
        recommendations.append(
            "Warm conditions are expected. Stay hydrated during "
            "prolonged outdoor activity."
        )

    # --------------------------------------------------------
    # Cold
    # --------------------------------------------------------

    if temperature_min <= 10:
        recommendations.append(
            "Cold conditions are expected. Warm clothing is recommended."
        )

    elif temperature_min <= 15:
        recommendations.append(
            "Cool conditions are expected. Consider wearing a light jacket."
        )

    # --------------------------------------------------------
    # Strong wind
    # --------------------------------------------------------

    if wind_speed >= 40:
        recommendations.append(
            "Strong winds are expected. Avoid unnecessary outdoor "
            "exposure and be cautious around trees and temporary structures."
        )

    elif wind_speed >= 25:
        recommendations.append(
            "Moderately strong winds are expected. Be cautious "
            "during outdoor activities."
        )

    # --------------------------------------------------------
    # Thunderstorm
    # --------------------------------------------------------

    if "thunderstorm" in condition_text:
        recommendations.append(
            "Thunderstorm conditions are possible. Avoid exposed "
            "outdoor areas and seek shelter if thunderstorms develop."
        )

    # --------------------------------------------------------
    # Activity-specific advice
    # --------------------------------------------------------

    if activity:

        activity_lower = activity.lower()

        if (
            "run" in activity_lower
            or "running" in activity_lower
        ):

            if (
                precipitation >= 2
                or rain_probability >= 60
                or "rain" in condition_text
                or "thunderstorm" in condition_text
            ):
                recommendations.append(
                    "Running may be uncomfortable because of "
                    "the expected wet or stormy conditions."
                )

            elif temperature_max >= 35:
                recommendations.append(
                    "Consider running during cooler hours because "
                    "of the high temperature."
                )

            elif wind_speed >= 30:
                recommendations.append(
                    "Strong winds may make running uncomfortable."
                )

            else:
                recommendations.append(
                    "Conditions appear generally suitable for running."
                )

        elif "travel" in activity_lower:

            if (
                precipitation >= 10
                or rain_probability >= 70
                or wind_speed >= 40
                or "thunderstorm" in condition_text
            ):
                recommendations.append(
                    "Travel may be affected by unfavorable weather "
                    "conditions. Check local warnings before departing."
                )

            else:
                recommendations.append(
                    "Weather conditions appear generally suitable for travel."
                )

        elif "outdoor" in activity_lower:

            if (
                precipitation >= 2
                or rain_probability >= 60
                or temperature_max >= 38
                or "thunderstorm" in condition_text
            ):
                recommendations.append(
                    "Outdoor activities may be uncomfortable or "
                    "disrupted by the weather."
                )

            else:
                recommendations.append(
                    "Conditions appear generally suitable for outdoor activities."
                )

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    if not recommendations:
        recommendations.append(
            "Weather conditions appear generally suitable "
            "for normal outdoor activities."
        )

    return recommendations