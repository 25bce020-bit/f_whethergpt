"""Sprint 14 GIS API tests. External geocoding/weather/IMD calls are mocked."""

import math
import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app import main as api
from app.services.gis_service import (
    current_weather_map,
    geographic_point,
    geojson_feature,
    validate_bounds,
    validate_coordinates,
    warning_map_alert,
)


LOCATION = {
    "name": "Ahmedabad", "country": "India", "admin1": "Gujarat",
    "latitude": 23.0225, "longitude": 72.5714,
}
CURRENT = {
    "time": "2026-09-15T09:00", "temperature_c": 29, "feels_like_c": 30,
    "humidity_percent": 60, "precipitation_mm": 0, "weather_code": 1,
    "condition": "Mainly clear", "wind_speed_kmh": 8,
}
FORECAST = [{"date": "2026-09-16", "temperature_max_c": 32, "temperature_min_c": 25, "precipitation_mm": 1, "weather_code": 61}]
HOURLY = [{"time": "2026-09-15T10:00", "temperature_c": 30, "precipitation_mm": 0, "rain_probability_percent": 10, "wind_speed_kmh": 8, "weather_code": 1}]


class GisServiceTests(unittest.TestCase):
    def test_coordinate_validation_accepts_valid_latitude_and_longitude(self):
        self.assertEqual(validate_coordinates(23.0225, 72.5714), (23.0225, 72.5714))

    def test_coordinate_validation_rejects_invalid_and_non_finite_values(self):
        for latitude, longitude in ((91, 0), (-91, 0), (0, 181), (0, -181), (math.nan, 0), (0, math.inf)):
            with self.subTest(latitude=latitude, longitude=longitude):
                with self.assertRaises(ValueError):
                    validate_coordinates(latitude, longitude)

    def test_geographic_point_preserves_geocoder_coordinates(self):
        point = geographic_point(LOCATION)
        self.assertEqual(point.model_dump(), {"latitude": 23.0225, "longitude": 72.5714, "name": "Ahmedabad", "country": "India", "state": "Gujarat"})

    def test_current_map_marker_and_geojson_are_frontend_ready(self):
        point = geographic_point(LOCATION)
        payload = current_weather_map(point, CURRENT)
        self.assertEqual(payload["marker"]["title"], "Ahmedabad")
        self.assertEqual(payload["marker"]["weather"], CURRENT)
        self.assertEqual(payload["geojson"]["geometry"]["coordinates"], [72.5714, 23.0225])

    def test_geojson_uses_longitude_latitude_order(self):
        feature = geojson_feature(geographic_point(LOCATION))
        self.assertEqual(feature["geometry"]["coordinates"], [72.5714, 23.0225])

    def test_warning_with_circle_uses_explicit_coordinate(self):
        alert = {"identifier": "imd-1", "event": "Heavy rain", "severity": "Severe", "areas": [{"circles": [{"latitude": 23.0, "longitude": 72.5, "radius_km": 30}]}]}
        mapped = warning_map_alert(alert)
        self.assertTrue(mapped["coordinates_available"])
        self.assertEqual(mapped["location"]["longitude"], 72.5)

    def test_warning_without_coordinate_is_not_geocoded_from_text(self):
        alert = {"identifier": "imd-2", "headline": "Warning for Ahmedabad", "areas": [{"description": "Ahmedabad"}]}
        mapped = warning_map_alert(alert)
        self.assertFalse(mapped["coordinates_available"])
        self.assertIsNone(mapped["location"])

    def test_bounds_validation(self):
        self.assertEqual(validate_bounds(30, 20, 80, 70).north, 30)
        with self.assertRaises(ValueError):
            validate_bounds(20, 30, 80, 70)


class GisEndpointTests(unittest.IsolatedAsyncioTestCase):
    async def test_location_to_coordinate_response_and_existing_location_search(self):
        with patch.object(api, "search_location", AsyncMock(return_value=[LOCATION])):
            self.assertEqual((await api.gis_location_search("Ahmedabad"))["latitude"], 23.0225)
            existing = await api.location_search("Ahmedabad")
        self.assertEqual(existing["results"][0]["name"], "Ahmedabad")

    async def test_current_weather_gis_response_reuses_existing_services_once(self):
        raw = {"current": {}, "timezone": "Asia/Kolkata"}
        with patch.object(api, "search_location", AsyncMock(return_value=[LOCATION])) as search, patch.object(api, "get_current_weather", AsyncMock(return_value=raw)) as current, patch.object(api, "format_current_weather", return_value=CURRENT):
            response = await api.gis_current_weather("Ahmedabad", None, None)
        self.assertEqual(response["location"]["name"], "Ahmedabad")
        self.assertEqual(response["weather"], CURRENT)
        search.assert_awaited_once_with("Ahmedabad")
        current.assert_awaited_once_with(23.0225, 72.5714)

    async def test_forecast_gis_response_reuses_existing_service(self):
        with patch.object(api, "search_location", AsyncMock(return_value=[LOCATION])), patch.object(api, "get_forecast", AsyncMock(return_value={})) as forecast, patch.object(api, "format_forecast", return_value=FORECAST):
            response = await api.gis_weather_forecast("Ahmedabad", None, None)
        self.assertEqual(response["forecast"], FORECAST)
        forecast.assert_awaited_once_with(23.0225, 72.5714)

    async def test_hourly_gis_response_reuses_existing_service(self):
        with patch.object(api, "search_location", AsyncMock(return_value=[LOCATION])), patch.object(api, "get_hourly_forecast", AsyncMock(return_value={})) as hourly, patch.object(api, "format_hourly_forecast", return_value=HOURLY):
            response = await api.gis_weather_hourly("Ahmedabad", None, None)
        self.assertEqual(response["hourly"], HOURLY)
        hourly.assert_awaited_once_with(23.0225, 72.5714)

    async def test_coordinates_take_priority_and_invalid_or_missing_location_is_clean(self):
        with patch.object(api, "search_location", AsyncMock()) as search, patch.object(api, "get_current_weather", AsyncMock(return_value={})), patch.object(api, "format_current_weather", return_value=CURRENT):
            response = await api.gis_current_weather("Ahmedabad", 12.0, 77.0)
        self.assertEqual(response["location"]["latitude"], 12.0)
        search.assert_not_awaited()
        with self.assertRaises(HTTPException) as missing:
            await api._resolve_gis_point(None, None, None)
        self.assertEqual(missing.exception.status_code, 422)
        with self.assertRaises(HTTPException) as invalid:
            await api._resolve_gis_point(None, 100.0, 77.0)
        self.assertEqual(invalid.exception.status_code, 422)
        with patch.object(api, "search_location", AsyncMock(return_value=[])):
            with self.assertRaises(HTTPException) as absent:
                await api._resolve_gis_point("Missing place", None, None)
        self.assertEqual(absent.exception.status_code, 404)

    async def test_official_warning_transformation_uses_imd_only(self):
        alerts = [{"identifier": "imd-1", "event": "Rain", "official": True, "areas": []}]
        with patch.object(api, "get_imd_cap_notifications", AsyncMock(return_value={})) as source, patch.object(api, "normalize_imd_cap_notifications", return_value=alerts):
            response = await api.gis_official_warnings()
        self.assertTrue(response["official"])
        self.assertEqual(response["alerts"][0]["source"], "IMD")
        source.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
