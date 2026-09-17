"""IMD Agromet / GKMS Agricultural Weather Advisory Service for WeatherGPT.

Provides grounded official agromet advisories from the India Meteorological Department (IMD)
Gramin Krishi Mausam Sewa (GKMS) scheme.

Design principles:
- No data simulation: Real API communication only.
- Strict bounded timeouts: Slow IMD calls will never block the system.
- Conservative fallback: When unavailable or unauthenticated, clearly states unavailability.
- Multilingual preservation: Retains regional language advisories alongside English.
- Crop matching: Matches user crop context against official advisory records.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timezone
from typing import Any

import httpx

from app.services.cache_service import get_or_load

logger = logging.getLogger(__name__)

IMD_AGROMET_BASE_URL = os.getenv("IMD_AGROMET_BASE_URL", "https://api.imd.gov.in/api/v1/agromet").rstrip("/")
MEGHDOOT_BASE_URL = os.getenv("IMD_MEGHDOOT_BASE_URL", "https://meghdoot.imd.gov.in/api").rstrip("/")
IMD_AGROMET_API_KEY = os.getenv("IMD_AGROMET_API_KEY", "").strip()
AGROMET_TIMEOUT_SECONDS = float(os.getenv("IMD_AGROMET_TIMEOUT_SECONDS", "5.0"))
AGROMET_CACHE_TTL = int(os.getenv("IMD_AGROMET_CACHE_TTL", "10800"))  # 3 hours


# Major Indian State to IMD State IDs mapping for deterministic location resolution
INDIAN_STATE_NAME_TO_ID: dict[str, int] = {
    "andaman and nicobar": 1,
    "andhra pradesh": 2,
    "arunachal pradesh": 3,
    "assam": 4,
    "bihar": 5,
    "chandigarh": 6,
    "chhattisgarh": 7,
    "dadra and nagar haveli": 8,
    "daman and diu": 9,
    "delhi": 10,
    "goa": 11,
    "gujarat": 24,
    "haryana": 12,
    "himachal pradesh": 13,
    "jammu and kashmir": 14,
    "jharkhand": 15,
    "karnataka": 16,
    "kerala": 17,
    "ladakh": 36,
    "lakshadweep": 18,
    "madhya pradesh": 19,
    "maharashtra": 20,
    "manipur": 21,
    "meghalaya": 22,
    "mizoram": 23,
    "nagaland": 25,
    "odisha": 26,
    "orissa": 26,
    "puducherry": 27,
    "pondicherry": 27,
    "punjab": 28,
    "rajasthan": 29,
    "sikkim": 30,
    "tamil nadu": 31,
    "telangana": 32,
    "tripura": 33,
    "uttar pradesh": 34,
    "uttarakhand": 35,
    "west bengal": 37,
}


def normalize_crop_name(crop: str | None) -> str | None:
    if not crop:
        return None
    c = crop.strip().lower()
    if c in ("paddy", "rice"):
        return "rice"
    return c


def resolve_agromet_location(
    *,
    latitude: float,
    longitude: float,
    location_name: str | None = None,
    state_name: str | None = None,
    country_code: str | None = "IN",
) -> dict[str, Any]:
    """Resolve WeatherGPT location into Agromet location identifiers.

    Returns deterministic state ID and metadata for Indian locations.
    """
    if country_code and country_code.upper() != "IN":
        return {
            "supported": False,
            "reason": "IMD Agromet / GKMS advisories are available for India only.",
            "state_id": None,
            "state_name": None,
            "district_name": location_name,
        }

    # Verify coordinates roughly match Indian territory (Lat 6°N - 38°N, Lon 68°E - 98°E)
    if not (6.0 <= latitude <= 38.0 and 68.0 <= longitude <= 98.0):
        return {
            "supported": False,
            "reason": "Coordinates are outside IMD Agromet coverage area.",
            "state_id": None,
            "state_name": None,
            "district_name": location_name,
        }

    state_id = None
    resolved_state = state_name or ""
    if state_name:
        clean_state = re.sub(r"[^a-zA-Z\s]", "", state_name).strip().lower()
        state_id = INDIAN_STATE_NAME_TO_ID.get(clean_state)

    if not state_id and location_name:
        clean_loc = re.sub(r"[^a-zA-Z\s]", "", location_name).strip().lower()
        state_id = INDIAN_STATE_NAME_TO_ID.get(clean_loc)
        if state_id:
            resolved_state = location_name

    return {
        "supported": True,
        "state_id": state_id,
        "state_name": resolved_state,
        "district_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
    }


def parse_iso_or_custom_date(val: Any) -> date | None:
    if not val or not isinstance(val, str):
        return None
    val_str = val.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(val_str[:10], fmt).date()
        except ValueError:
            continue
    return None


def normalize_agromet_payload(
    raw_data: Any,
    *,
    location_meta: dict[str, Any],
    crop_filter: str | None = None,
) -> dict[str, Any]:
    """Normalize raw IMD Agromet / Meghdoot response into internal WeatherGPT structure."""
    now_iso = datetime.now(timezone.utc).isoformat()
    today_dt = date.today()

    if not raw_data:
        return {
            "available": False,
            "status": "empty",
            "source": "IMD Agromet/GKMS",
            "location": {
                "state": location_meta.get("state_name"),
                "district": location_meta.get("district_name"),
                "latitude": location_meta.get("latitude"),
                "longitude": location_meta.get("longitude"),
            },
            "advisories": [],
            "source_attribution": {
                "provider": "India Meteorological Department (IMD) - GKMS",
                "url": "https://agromet.imd.gov.in",
                "retrieved_at": now_iso,
            },
            "note": "Official IMD Agromet advisory was not found for this location.",
        }

    # Extract raw list of advisory items from dictionary or list wrapper
    raw_list: list[dict[str, Any]] = []
    if isinstance(raw_data, list):
        raw_list = [x for x in raw_data if isinstance(x, dict)]
    elif isinstance(raw_data, dict):
        for key in ("ObjCropAdvisoryDetailsList", "CropAdvisoryDetails", "advisories", "data", "results"):
            candidate = raw_data.get(key)
            if isinstance(candidate, list):
                raw_list = [x for x in candidate if isinstance(x, dict)]
                break
        if not raw_list and ("Recommendations" in raw_data or "recommendation" in raw_data):
            raw_list = [raw_data]

    target_crop = normalize_crop_name(crop_filter)
    normalized_advisories: list[dict[str, Any]] = []

    for item in raw_list:
        adv_crop = item.get("CropName") or item.get("crop_name") or item.get("Crop") or item.get("crop")
        norm_adv_crop = normalize_crop_name(str(adv_crop)) if adv_crop else None

        # Crop matching: If user requested a specific crop, filter out mismatches
        # (while preserving general/district wide advisories where crop is not specified)
        if target_crop and norm_adv_crop and target_crop != norm_adv_crop:
            continue

        rec_en = item.get("Recommendations") or item.get("recommendation") or item.get("AgroAdvisoryDetails") or ""
        rec_reg = item.get("RecommendationsRegional") or item.get("recommendation_regional") or item.get("AgroAdvisoryDetailsRegional") or ""
        cond_en = item.get("WeatherCondition") or item.get("weather_condition") or ""
        cond_reg = item.get("WeatherConditionRegional") or item.get("weather_condition_regional") or ""

        # Validity check: Ignore advisories that expired in the past
        valid_until_str = item.get("PeriodEndDate") or item.get("valid_until") or item.get("EndDate")
        valid_until_dt = parse_iso_or_custom_date(valid_until_str)
        if valid_until_dt and valid_until_dt < today_dt:
            continue

        valid_from_str = item.get("PeriodStartDate") or item.get("valid_from") or item.get("StartDate")

        normalized_advisories.append({
            "id": item.get("CropAdvisoryID") or item.get("id"),
            "title": item.get("Title") or item.get("title") or (f"Advisory for {adv_crop}" if adv_crop else "District Agromet Advisory"),
            "crop": adv_crop,
            "variety": item.get("VarietyName") or item.get("variety"),
            "state": item.get("State") or location_meta.get("state_name"),
            "district": item.get("District") or location_meta.get("district_name"),
            "block": item.get("Block"),
            "weather_condition": str(cond_en).strip(),
            "weather_condition_regional": str(cond_reg).strip() if cond_reg else None,
            "recommendation": str(rec_en).strip(),
            "recommendation_regional": str(rec_reg).strip() if rec_reg else None,
            "language": item.get("RegionalLanguage") or item.get("language"),
            "valid_from": valid_from_str,
            "valid_until": valid_until_str,
            "updated_at": item.get("RefreshDateTime") or item.get("CreatedDate") or now_iso,
        })

    is_available = len(normalized_advisories) > 0
    return {
        "available": is_available,
        "status": "available" if is_available else "empty",
        "source": "IMD Agromet/GKMS",
        "location": {
            "state": location_meta.get("state_name"),
            "district": location_meta.get("district_name"),
            "latitude": location_meta.get("latitude"),
            "longitude": location_meta.get("longitude"),
        },
        "advisories": normalized_advisories,
        "source_attribution": {
            "provider": "India Meteorological Department (IMD) - GKMS / Agromet Advisory",
            "url": "https://agromet.imd.gov.in",
            "retrieved_at": now_iso,
        },
        "note": (
            f"Retrieved {len(normalized_advisories)} official IMD Agromet advisory record(s)."
            if is_available
            else "No active matching IMD Agromet advisory available for this location/crop."
        ),
    }


async def fetch_raw_agromet_data(
    location_meta: dict[str, Any],
    crop: str | None = None,
) -> dict[str, Any] | list[Any] | None:
    """Execute live HTTP request to official IMD Agromet / Meghdoot endpoints with explicit timeouts."""
    if not location_meta.get("supported"):
        return None

    headers = {
        "User-Agent": "WeatherGPT-Agromet-Service/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if IMD_AGROMET_API_KEY:
        headers["Authorization"] = f"Bearer {IMD_AGROMET_API_KEY}"
        headers["X-API-Key"] = IMD_AGROMET_API_KEY

    lat = location_meta.get("latitude")
    lon = location_meta.get("longitude")
    state_id = location_meta.get("state_id")

    # 1. Try unified IMD API Gateway if API key or endpoint configured
    if IMD_AGROMET_API_KEY or "api.imd.gov.in" in IMD_AGROMET_BASE_URL:
        try:
            params: dict[str, Any] = {}
            if state_id:
                params["state_id"] = state_id
            if lat is not None and lon is not None:
                params["lat"] = lat
                params["lon"] = lon
            if crop:
                params["crop"] = crop

            async with httpx.AsyncClient(timeout=AGROMET_TIMEOUT_SECONDS) as client:
                res = await client.get(IMD_AGROMET_BASE_URL, params=params, headers=headers)
                if res.status_code == 200:
                    return res.json()
                elif res.status_code in (401, 403):
                    logger.warning(
                        "IMD Agromet API returned %s Unauthorized. Requires registered IMD credentials.",
                        res.status_code,
                    )
                    return None
        except httpx.TimeoutException:
            logger.warning("IMD Agromet API request timed out after %.1fs", AGROMET_TIMEOUT_SECONDS)
            return None
        except Exception as err:
            logger.warning("IMD Agromet API request failed: %s", err)

    # 2. Try Meghdoot Web API endpoints
    try:
        async with httpx.AsyncClient(timeout=AGROMET_TIMEOUT_SECONDS) as client:
            payload: dict[str, Any] = {
                "Latitude": str(lat) if lat is not None else "",
                "Longitude": str(lon) if lon is not None else "",
            }
            if state_id:
                payload["StateID"] = state_id

            res = await client.post(
                f"{MEGHDOOT_BASE_URL}/CropAdvisory/GetGPSCropAdvisoryTopValues",
                json=payload,
                headers=headers,
            )
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, (dict, list)):
                    return data
    except httpx.TimeoutException:
        logger.warning("Meghdoot Agromet request timed out after %.1fs", AGROMET_TIMEOUT_SECONDS)
        return None
    except Exception as err:
        logger.warning("Meghdoot Agromet request failed: %s", err)

    return None


async def get_agromet_advisory(
    *,
    latitude: float,
    longitude: float,
    location_name: str | None = None,
    state_name: str | None = None,
    crop: str | None = None,
    country_code: str | None = "IN",
) -> dict[str, Any]:
    """Retrieve normalized, cached IMD Agromet / GKMS advisory data for a location.

    Guarantees:
    - Never raises unhandled exceptions to callers.
    - Strictly bounded response times with caching.
    - Distinguishes authentic IMD advisories from unavailable states.
    """
    loc_meta = resolve_agromet_location(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        state_name=state_name,
        country_code=country_code,
    )

    if not loc_meta.get("supported"):
        return {
            "available": False,
            "status": "unsupported_location",
            "source": "IMD Agromet/GKMS",
            "location": {
                "state": state_name,
                "district": location_name,
                "latitude": latitude,
                "longitude": longitude,
            },
            "advisories": [],
            "source_attribution": {
                "provider": "India Meteorological Department (IMD) - GKMS",
                "url": "https://agromet.imd.gov.in",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
            "note": loc_meta.get("reason", "Location is outside IMD Agromet coverage area."),
        }

    norm_crop = normalize_crop_name(crop) or "all"
    cache_key = f"agromet:{loc_meta.get('state_id') or 'geo'}:{latitude:.2f}:{longitude:.2f}:{norm_crop}"

    async def _load() -> dict[str, Any]:
        raw = await fetch_raw_agromet_data(loc_meta, crop=crop)
        return normalize_agromet_payload(raw, location_meta=loc_meta, crop_filter=crop)

    try:
        cached = await get_or_load(
            cache_key,
            source="IMD Agromet/GKMS",
            ttl_seconds=AGROMET_CACHE_TTL,
            loader=_load,
        )
        return cached["data"]
    except Exception as exc:
        logger.warning("Error fetching or caching Agromet advisory: %s", exc)
        return normalize_agromet_payload(None, location_meta=loc_meta, crop_filter=crop)
