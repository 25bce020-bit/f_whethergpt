import base64
import math
import os
import xml.etree.ElementTree as ET

import httpx
import truststore

from app.services.cache_service import get_or_load


truststore.inject_into_ssl()


IMD_WIS2_MESSAGES_URL = (
    "https://wis2box.imd.gov.in/oapi/collections/messages/items"
)

IMD_CAP_METADATA_ID = (
    "urn:wmo:md:in-imd:cap_alerts"
)
IMD_TTL = int(os.getenv("IMD_CACHE_TTL", "300"))


async def get_imd_cap_notifications(limit: int = 20):
    params = {
        "limit": limit,
        "metadata_id": IMD_CAP_METADATA_ID,
    }

    async def load():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                IMD_WIS2_MESSAGES_URL,
                params=params,
                headers={"Accept": "application/geo+json"},
            )
        response.raise_for_status()
        return response.json()

    cached = await get_or_load(
        f"imd:cap:raw:{limit}",
        "India Meteorological Department WIS2/CAP",
        IMD_TTL,
        load,
    )
    return cached["data"]


def _decode_content(content):
    if not content:
        return None

    if isinstance(content, dict):
        value = content.get("value")
        encoding = content.get("encoding")

        if encoding == "base64" and value:
            try:
                return base64.b64decode(
                    value
                ).decode(
                    "utf-8",
                    errors="replace",
                )
            except Exception:
                return None

        return value

    return content

def alert_mentions_location(
    alert: dict,
    location_name: str | None = None,
    state_name: str | None = None,
):
    location_name = (
        location_name or ""
    ).strip().lower()

    state_name = (
        state_name or ""
    ).strip().lower()

    if not location_name and not state_name:
        return False

    search_text = " ".join([
        str(alert.get("event") or ""),
        str(alert.get("headline") or ""),
        str(alert.get("description") or ""),
    ]).lower()

    for area in alert.get("areas", []):
        search_text += " "
        search_text += str(
            area.get("description") or ""
        ).lower()

    location_match = (
        location_name
        and location_name in search_text
    )

    state_match = (
        state_name
        and state_name in search_text
    )

    return bool(
        location_match
        or state_match
    )

def _find_text(element, tag):
    node = element.find(
        f".//{{*}}{tag}"
    )

    if node is None:
        return None

    return node.text


def _parse_polygon(value):
    if not value:
        return []

    points = []

    # CAP polygon format:
    # "lat,lon lat,lon lat,lon ..."
    for pair in value.split():
        try:
            latitude, longitude = pair.split(",")

            points.append(
                (
                    float(latitude),
                    float(longitude),
                )
            )
        except (ValueError, TypeError):
            continue

    return points


def _parse_circle(value):
    if not value:
        return None

    # CAP circle format:
    # "latitude,longitude radius_in_km"
    try:
        parts = value.split()

        latitude, longitude = parts[0].split(",")

        radius_km = float(parts[1])

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "radius_km": radius_km,
        }

    except (ValueError, IndexError):
        return None


def _parse_cap_xml(xml_text):
    if not xml_text:
        return None

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None

    info = root.find(
        ".//{*}info"
    )

    if info is None:
        return None

    alert = {
        "identifier": _find_text(
            root,
            "identifier",
        ),
        "sender": _find_text(
            root,
            "sender",
        ),
        "sent": _find_text(
            root,
            "sent",
        ),
        "status": _find_text(
            root,
            "status",
        ),
        "message_type": _find_text(
            root,
            "msgType",
        ),
        "event": _find_text(
            info,
            "event",
        ),
        "severity": _find_text(
            info,
            "severity",
        ),
        "urgency": _find_text(
            info,
            "urgency",
        ),
        "certainty": _find_text(
            info,
            "certainty",
        ),
        "headline": _find_text(
            info,
            "headline",
        ),
        "description": _find_text(
            info,
            "description",
        ),
        "instruction": _find_text(
            info,
            "instruction",
        ),
        "areas": [],
    }

    for area in info.findall(
        ".//{*}area"
    ):
        area_data = {
            "description": _find_text(
                area,
                "areaDesc",
            ),
            "polygons": [],
            "circles": [],
        }

        for polygon in area.findall(
            ".//{*}polygon"
        ):
            parsed = _parse_polygon(
                polygon.text
            )

            if parsed:
                area_data["polygons"].append(
                    parsed
                )

        for circle in area.findall(
            ".//{*}circle"
        ):
            parsed = _parse_circle(
                circle.text
            )

            if parsed:
                area_data["circles"].append(
                    parsed
                )

        alert["areas"].append(
            area_data
        )

    return alert


def normalize_imd_cap_notifications(data):
    if not data:
        return []

    features = data.get(
        "features",
        [],
    )

    alerts = []

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        metadata_id = properties.get(
            "metadata_id"
        )

        if metadata_id != IMD_CAP_METADATA_ID:
            continue

        content = properties.get(
            "content"
        )

        xml_text = _decode_content(
            content
        )

        alert = _parse_cap_xml(
            xml_text
        )

        if alert:
            alert["source"] = (
                "India Meteorological Department"
            )

            alert["official"] = True

            alerts.append(
                alert
            )

    return alerts


def _point_in_polygon(
    latitude: float,
    longitude: float,
    polygon: list,
):
    if len(polygon) < 3:
        return False

    inside = False

    j = len(polygon) - 1

    for i in range(len(polygon)):
        lat_i, lon_i = polygon[i]
        lat_j, lon_j = polygon[j]

        intersects = (
            (lon_i > longitude)
            != (lon_j > longitude)
        ) and (
            latitude
            < (
                (lat_j - lat_i)
                * (longitude - lon_i)
                / (
                    (lon_j - lon_i)
                    or 1e-12
                )
                + lat_i
            )
        )

        if intersects:
            inside = not inside

        j = i

    return inside


def _distance_km(
    latitude1,
    longitude1,
    latitude2,
    longitude2,
):
    earth_radius_km = 6371.0

    lat1 = math.radians(latitude1)
    lat2 = math.radians(latitude2)

    delta_lat = math.radians(
        latitude2 - latitude1
    )

    delta_lon = math.radians(
        longitude2 - longitude1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    return (
        2
        * earth_radius_km
        * math.asin(
            math.sqrt(a)
        )
    )


def alert_affects_location(
    alert: dict,
    latitude: float,
    longitude: float,
):
    for area in alert.get(
        "areas",
        [],
    ):
        for polygon in area.get(
            "polygons",
            [],
        ):
            if _point_in_polygon(
                latitude,
                longitude,
                polygon,
            ):
                return True

        for circle in area.get(
            "circles",
            [],
        ):
            distance = _distance_km(
                latitude,
                longitude,
                circle["latitude"],
                circle["longitude"],
            )

            if distance <= circle["radius_km"]:
                return True

    return False

def alert_mentions_location(
    alert: dict,
    location_name: str | None = None,
    state_name: str | None = None,
):
    location_name = (
        location_name or ""
    ).strip().lower()

    state_name = (
        state_name or ""
    ).strip().lower()

    if not location_name and not state_name:
        return False

    search_text = " ".join([
        str(alert.get("event") or ""),
        str(alert.get("headline") or ""),
        str(alert.get("description") or ""),
    ]).lower()

    for area in alert.get("areas", []):
        search_text += " "
        search_text += str(
            area.get("description") or ""
        ).lower()

    location_match = (
        location_name
        and location_name in search_text
    )

    state_match = (
        state_name
        and state_name in search_text
    )

    return bool(
        location_match
        or state_match
    )
def filter_alerts_for_location(
    alerts: list,
    latitude: float,
    longitude: float,
    location_name: str | None = None,
    state_name: str | None = None,
):
    matching_alerts = []

    for alert in alerts:
        geographic_match = alert_affects_location(
            alert,
            latitude,
            longitude,
        )

        text_match = alert_mentions_location(
            alert,
            location_name,
            state_name,
        )

        if geographic_match or text_match:
            matching_alerts.append(alert)

    return matching_alerts
