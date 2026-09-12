from typing import Any


def is_number(value):
    return isinstance(
        value,
        (int, float),
    )


def validate_coordinates(
    latitude,
    longitude,
):

    errors = []

    if not is_number(latitude):
        errors.append(
            "Latitude must be numeric."
        )

    elif not -90 <= latitude <= 90:
        errors.append(
            "Latitude outside valid range."
        )

    if not is_number(longitude):
        errors.append(
            "Longitude must be numeric."
        )

    elif not -180 <= longitude <= 180:
        errors.append(
            "Longitude outside valid range."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_open_meteo_data(
    data: dict[str, Any],
):

    errors = []

    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": [
                "Open-Meteo response is not an object."
            ],
        }

    if "latitude" not in data:
        errors.append(
            "Missing latitude."
        )

    if "longitude" not in data:
        errors.append(
            "Missing longitude."
        )

    if not data.get("current"):
        errors.append(
            "Missing current weather data."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_gfs_data(
    data: dict[str, Any],
):

    errors = []

    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": [
                "GFS response is not an object."
            ],
        }

    if not data.get("hourly"):
        errors.append(
            "Missing GFS hourly data."
        )

    if not data.get("daily"):
        errors.append(
            "Missing GFS daily data."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def validate_cap_alerts(
    alerts: list,
):

    if not isinstance(alerts, list):
        return {
            "valid": False,
            "errors": [
                "CAP alerts must be a list."
            ],
        }

    valid_alerts = []

    for alert in alerts:

        if not isinstance(alert, dict):
            continue

        if (
            alert.get("identifier")
            or alert.get("event")
            or alert.get("headline")
        ):
            valid_alerts.append(alert)

    return {
        "valid": True,
        "errors": [],
        "alerts": valid_alerts,
    }