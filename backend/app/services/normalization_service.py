from datetime import datetime, timezone


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def normalize_open_meteo(
    data: dict,
    location: dict,
):

    current = data.get(
        "current",
        {},
    )

    return {
        "source": "Open-Meteo",
        "provider_type": "weather_api",
        "location": {
            "name": location.get("name"),
            "state": location.get("state"),
            "country": location.get(
                "country"
            ),
            "latitude": location.get(
                "latitude"
            ),
            "longitude": location.get(
                "longitude"
            ),
        },
        "observed_at": current.get(
            "time"
        ),
        "ingested_at": utc_now(),

        "temperature_c": current.get(
            "temperature_2m"
        ),

        "apparent_temperature_c":
            current.get(
                "apparent_temperature"
            ),

        "humidity_percent":
            current.get(
                "relative_humidity_2m"
            ),

        "precipitation_mm":
            current.get(
                "precipitation"
            ),

        "weather_code":
            current.get(
                "weather_code"
            ),

        "wind_speed_kmh":
            current.get(
                "wind_speed_10m"
            ),

        "wind_direction_degrees":
            current.get(
                "wind_direction_10m"
            ),
    }


def normalize_gfs(
    formatted_gfs: dict,
    location: dict,
):

    return {
        "source": "NCEP GFS",
        "provider": "NOAA",
        "provider_type":
            "numerical_weather_prediction",

        "location": {
            "name": location.get("name"),
            "state": location.get("state"),
            "country": location.get(
                "country"
            ),
            "latitude": location.get(
                "latitude"
            ),
            "longitude": location.get(
                "longitude"
            ),
        },

        "ingested_at": utc_now(),

        "hourly":
            formatted_gfs.get(
                "hourly",
                []
            ),

        "daily":
            formatted_gfs.get(
                "daily",
                []
            ),
    }


def normalize_cap_alerts(
    alerts: list,
):

    normalized = []

    for alert in alerts:

        normalized.append({
            **alert,

            "source":
                "India Meteorological Department",

            "provider_type":
                "official_warning",

            "official": True,

            "ingested_at":
                utc_now(),
        })

    return normalized