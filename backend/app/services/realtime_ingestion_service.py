import asyncio
import logging
import os

from app.services.database_service import save_official_alert
import httpx

from app.services.cache_service import (
    set_cache,
    get_cache,
    get_or_load,
)
from app.services.database_service import (
    save_official_alert,
    save_ingestion_log,
)
from app.services.database_service import (
    save_weather_record,
    save_official_alert,
    save_ingestion_log,
)
from app.services.validation_service import (
    validate_coordinates,
    validate_open_meteo_data,
    validate_gfs_data,
    validate_cap_alerts,
)

from app.services.normalization_service import (
    normalize_open_meteo,
    normalize_gfs,
    normalize_cap_alerts,
)

from app.services.location_service import (
    search_location,
)

from app.services.nwp_service import (
    get_gfs_forecast,
    format_gfs_forecast,
)

from app.services.imd_cap_service import (
    get_imd_cap_notifications,
    normalize_imd_cap_notifications,
)


OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


OPEN_METEO_TTL = int(
    os.getenv(
        "OPEN_METEO_CACHE_TTL",
        "900",
    )
)
logger = logging.getLogger(__name__)

GFS_TTL = int(
    os.getenv(
        "GFS_CACHE_TTL",
        "3600",
    )
)

IMD_TTL = int(
    os.getenv(
        "IMD_CACHE_TTL",
        "300",
    )
)


TRACKED_LOCATIONS = [
    location.strip()
    for location in os.getenv(
        "REALTIME_LOCATIONS",
        "Delhi,Mumbai,Kolkata",
    ).split(",")
    if location.strip()
]


def location_cache_id(
    latitude: float,
    longitude: float,
):
    return (
        f"{latitude:.4f}:"
        f"{longitude:.4f}"
    )


async def resolve_location(
    location_name: str,
):

    results = await search_location(
        location_name
    )

    if not results:
        return None

    result = results[0]

    return {
        "name": result.get("name"),
        "country": result.get(
            "country"
        ),
        "state": result.get(
            "admin1"
        ),
        "latitude": result.get(
            "latitude"
        ),
        "longitude": result.get(
            "longitude"
        ),
    }


async def fetch_open_meteo(
    latitude: float,
    longitude: float,
):

    validation = validate_coordinates(
        latitude,
        longitude,
    )

    if not validation["valid"]:
        raise ValueError(
            validation["errors"]
        )

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m,"
            "wind_direction_10m"
        ),

        "timezone":
            "Asia/Kolkata",
    }

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.get(
            OPEN_METEO_URL,
            params=params,
        )

        response.raise_for_status()

        return response.json()


async def ingest_open_meteo_location(
    location: dict,
):
    latitude = location["latitude"]
    longitude = location["longitude"]
    cache_key = f"open_meteo:{location_cache_id(latitude, longitude)}"

    async def load():
        raw = await fetch_open_meteo(latitude, longitude)
        validation = validate_open_meteo_data(raw)
        if not validation["valid"]:
            raise ValueError(validation["errors"])
        normalized = normalize_open_meteo(raw, location)
        await save_weather_record(
            source="Open-Meteo",
            location_name=location.get("name"),
            latitude=latitude,
            longitude=longitude,
            temperature_c=normalized.get("temperature_c"),
            apparent_temperature_c=normalized.get("apparent_temperature_c"),
            humidity_percent=normalized.get("humidity_percent"),
            precipitation_mm=normalized.get("precipitation_mm"),
            wind_speed_kmh=normalized.get("wind_speed_kmh"),
            weather_code=normalized.get("weather_code"),
            observed_at=normalized.get("observed_at"),
        )
        return {"raw": raw, "normalized": normalized}

    cached = await get_or_load(cache_key, "Open-Meteo", OPEN_METEO_TTL, load)
    return cached["data"]["normalized"]


async def ingest_gfs_location(
    location: dict,
):
    latitude = location["latitude"]
    longitude = location["longitude"]
    cache_key = f"gfs:ingestion:{location_cache_id(latitude, longitude)}"

    async def load():
        raw = await get_gfs_forecast(latitude, longitude)
        validation = validate_gfs_data(raw)
        if not validation["valid"]:
            raise ValueError(validation["errors"])
        formatted = format_gfs_forecast(raw)
        return {
            "raw": raw,
            "formatted": formatted,
            "normalized": normalize_gfs(formatted, location),
        }

    cached = await get_or_load(cache_key, "NCEP GFS", GFS_TTL, load)
    return cached["data"]["normalized"]


async def ingest_imd_cap():
    async def load():
        raw = await get_imd_cap_notifications(limit=50)
        parsed = normalize_imd_cap_notifications(raw)
        validation = validate_cap_alerts(parsed)
        normalized = normalize_cap_alerts(validation.get("alerts", []))
        for alert in normalized:
            await save_official_alert(alert)
        await save_ingestion_log(
            source="IMD WIS2/CAP",
            status="success",
            message=f"Stored {len(normalized)} alerts.",
        )
        return {"raw": raw, "alerts": normalized}

    cached = await get_or_load(
        "imd:cap",
        "India Meteorological Department",
        IMD_TTL,
        load,
    )
    return cached["data"]["alerts"]


async def refresh_location(
    location_name: str,
):

    location = await resolve_location(
        location_name
    )

    if not location:
        return {
            "success": False,
            "location":
                location_name,
            "error":
                "Location not found.",
        }

    results = {
        "success": True,
        "location": location,
        "open_meteo": None,
        "gfs": None,
        "errors": [],
    }

    try:

        results["open_meteo"] = (
            await ingest_open_meteo_location(
                location
            )
        )

    except Exception as exc:

        results["errors"].append({
            "source": "Open-Meteo",
            "error": str(exc),
        })

    try:

        results["gfs"] = (
            await ingest_gfs_location(
                location
            )
        )

    except Exception as exc:

        results["errors"].append({
            "source": "GFS",
            "error": str(exc),
        })

    return results


async def get_cached_location_data(
    location_name: str,
    refresh_if_missing: bool = True,
):

    location = await resolve_location(
        location_name
    )

    if not location:
        return None

    cache_id = location_cache_id(
        location["latitude"],
        location["longitude"],
    )

    open_meteo = await get_cache(
        f"open_meteo:{cache_id}"
    )

    gfs = await get_cache(
        f"gfs:ingestion:{cache_id}"
    )

    if (
        refresh_if_missing
        and (
            open_meteo is None
            or gfs is None
        )
    ):

        await refresh_location(
            location_name
        )

        open_meteo = (
            await get_cache(
                f"open_meteo:{cache_id}"
            )
        )

        gfs = (
            await get_cache(
                f"gfs:ingestion:{cache_id}"
            )
        )

    return {
        "location": location,
        "open_meteo": open_meteo,
        "gfs": gfs,
    }


async def get_cached_imd_alerts(
    refresh_if_missing=True,
):

    cached = await get_cache(
        "imd:cap"
    )

    if (
        cached is None
        and refresh_if_missing
    ):

        await ingest_imd_cap()

        cached = await get_cache(
            "imd:cap"
        )

    return cached


async def refresh_all_tracked_locations():

    results = []

    for location_name in TRACKED_LOCATIONS:

        try:

            result = (
                await refresh_location(
                    location_name
                )
            )

            results.append(
                result
            )

        except Exception as exc:

            results.append({
                "success": False,
                "location":
                    location_name,
                "error": str(exc),
            })

    return results


async def open_meteo_refresh_loop():

    while True:

        try:

            for name in TRACKED_LOCATIONS:

                location = (
                    await resolve_location(
                        name
                    )
                )

                if location:

                    await (
                        ingest_open_meteo_location(
                            location
                        )
                    )

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.error("Open-Meteo ingestion error")

        await asyncio.sleep(
            OPEN_METEO_TTL
        )


async def gfs_refresh_loop():

    while True:

        try:

            for name in TRACKED_LOCATIONS:

                location = (
                    await resolve_location(
                        name
                    )
                )

                if location:

                    await (
                        ingest_gfs_location(
                            location
                        )
                    )

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.error("GFS ingestion error")

        await asyncio.sleep(
            GFS_TTL
        )


async def imd_refresh_loop():

    while True:

        try:

            await ingest_imd_cap()

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.error("IMD CAP ingestion error")

        await asyncio.sleep(
            IMD_TTL
        )


def start_realtime_ingestion():

    tasks = [
        asyncio.create_task(
            open_meteo_refresh_loop()
        ),
        asyncio.create_task(
            gfs_refresh_loop()
        ),
        asyncio.create_task(
            imd_refresh_loop()
        ),
    ]

    return tasks


async def stop_realtime_ingestion(
    tasks,
):

    for task in tasks:
        task.cancel()

    await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )
