import httpx


IMD_DISTRICT_WARNING_URL = (
    "https://mausam.imd.gov.in/api/warnings_district_api.php"
)


WARNING_CODES = {
    1: "No Warning",
    2: "Heavy Rain",
    3: "Heavy Snow",
    4: "Thunderstorm & Lightning, Squall etc",
    5: "Hailstorm",
    6: "Dust Storm",
    7: "Dust Raising Winds",
    8: "Strong Surface Winds",
    9: "Heat Wave",
    10: "Hot Day",
    11: "Warm Night",
    12: "Cold Wave",
    13: "Cold Day",
    14: "Ground Frost",
    15: "Fog",
    16: "Very Heavy Rain",
    17: "Extremely Heavy Rain",
}


COLOR_LEVELS = {
    1: "red",
    2: "orange",
    3: "yellow",
    4: "green",
}


async def get_district_warning(district_id: int):
    params = {
        "id": district_id
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            IMD_DISTRICT_WARNING_URL,
            params=params,
        )

        response.raise_for_status()

        return response.json()


def _parse_warning_codes(value):
    if value is None:
        return []

    if isinstance(value, int):
        return [value]

    if isinstance(value, float):
        return [int(value)]

    if isinstance(value, list):
        result = []

        for item in value:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue

        return result

    if isinstance(value, str):
        result = []

        for item in value.split(","):
            item = item.strip()

            if not item:
                continue

            try:
                result.append(int(item))
            except ValueError:
                continue

        return result

    return []


def normalize_district_warning(data):
    if not data:
        return {
            "source": "India Meteorological Department",
            "district": None,
            "issued_date": None,
            "days": [],
        }

    if isinstance(data, list):
        item = data[0] if data else {}
    elif isinstance(data, dict):
        item = data
    else:
        item = {}

    days = []

    for day_number in range(1, 6):
        warning_value = item.get(f"Day_{day_number}")
        color_value = item.get(f"Day{day_number}_Color")

        codes = _parse_warning_codes(warning_value)

        warnings = []

        for code in codes:
            warnings.append({
                "code": code,
                "description": WARNING_CODES.get(
                    code,
                    "Unknown weather warning",
                ),
            })

        try:
            color_code = int(color_value)
        except (TypeError, ValueError):
            color_code = None

        days.append({
            "day": day_number,
            "warnings": warnings,
            "color_code": color_code,
            "severity": COLOR_LEVELS.get(
                color_code,
                "unknown",
            ),
        })

    return {
        "source": "India Meteorological Department",
        "district": (
            item.get("District")
            or item.get("district")
        ),
        "object_id": (
            item.get("Obj_id")
            or item.get("obj_id")
        ),
        "issued_date": (
            item.get("Date")
            or item.get("date")
        ),
        "issued_time_utc": (
            item.get("UTC")
            or item.get("utc")
        ),
        "days": days,
    }