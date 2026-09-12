import asyncio
import unittest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from sqlalchemy import delete

from app.services import cache_service
from app.services import imd_cap_service, nwp_service, realtime_ingestion_service
from app.services import weather_service
from app.services import database_service
from app.services import historical_service, location_service, llm_service
from app.database import AsyncSessionLocal, close_db
from app.models import OfficialAlert
from app import main as api


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class FakeClient:
    calls = 0
    response_data = {}

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, *args, **kwargs):
        type(self).calls += 1
        return FakeResponse(type(self).response_data)


class CachePerformanceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await cache_service.clear_cache()

    async def test_miss_hit_expiry_and_refresh(self):
        calls = 0

        async def load():
            nonlocal calls
            calls += 1
            return {"value": calls}

        first = await cache_service.get_or_load("test:ttl", "test", 1, load)
        second = await cache_service.get_or_load("test:ttl", "test", 1, load)
        await asyncio.sleep(1.05)
        third = await cache_service.get_or_load("test:ttl", "test", 1, load)

        self.assertEqual(first["data"]["value"], 1)
        self.assertEqual(second["data"]["value"], 1)
        self.assertEqual(third["data"]["value"], 2)
        self.assertEqual(calls, 2)
        metrics = await cache_service.get_cache_metrics()
        self.assertGreaterEqual(metrics["hits"], 1)
        self.assertGreaterEqual(metrics["expired"], 1)

    async def test_concurrent_requests_share_one_loader(self):
        calls = 0

        async def load():
            nonlocal calls
            calls += 1
            await asyncio.sleep(0.05)
            return {"call": calls}

        results = await asyncio.gather(*[
            cache_service.get_or_load("test:concurrent", "test", 60, load)
            for _ in range(8)
        ])

        self.assertEqual(calls, 1)
        self.assertTrue(all(result["data"]["call"] == 1 for result in results))
        metrics = await cache_service.get_cache_metrics()
        self.assertEqual(metrics["upstream_requests"], 1)
        self.assertEqual(metrics["coalesced_requests"], 7)


class UpstreamServiceCacheTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await cache_service.clear_cache()
        FakeClient.calls = 0

    async def test_current_weather_cache_prevents_second_request(self):
        FakeClient.response_data = {
            "timezone": "UTC",
            "current": {
                "time": "2026-09-12T00:00",
                "temperature_2m": 25,
                "relative_humidity_2m": 60,
                "apparent_temperature": 25,
                "precipitation": 0,
                "weather_code": 0,
                "wind_speed_10m": 5,
                "wind_direction_10m": 90,
            },
        }
        with patch.object(weather_service.httpx, "AsyncClient", FakeClient):
            await weather_service.get_current_weather(28.6139, 77.2090)
            await weather_service.get_current_weather(28.6139, 77.2090)
        self.assertEqual(FakeClient.calls, 1)

    async def test_gfs_cache_prevents_second_request(self):
        FakeClient.response_data = {"hourly": {}, "daily": {}}
        with patch.object(nwp_service.httpx, "AsyncClient", FakeClient):
            await nwp_service.get_gfs_forecast(28.6139, 77.2090)
            await nwp_service.get_gfs_forecast(28.6139, 77.2090)
        self.assertEqual(FakeClient.calls, 1)

    async def test_forecast_hourly_historical_and_location_caches(self):
        FakeClient.response_data = {"daily": {"time": []}, "timezone": "UTC"}
        with patch.object(weather_service.httpx, "AsyncClient", FakeClient):
            await weather_service.get_forecast(28.6139, 77.2090)
            await weather_service.get_forecast(28.6139, 77.2090)
        self.assertEqual(FakeClient.calls, 1)

        FakeClient.calls = 0
        FakeClient.response_data = {"hourly": {"time": []}, "timezone": "UTC"}
        with patch.object(weather_service.httpx, "AsyncClient", FakeClient):
            await weather_service.get_hourly_forecast(28.6139, 77.2090)
            await weather_service.get_hourly_forecast(28.6139, 77.2090)
        self.assertEqual(FakeClient.calls, 1)

        FakeClient.calls = 0
        FakeClient.response_data = {"daily": {"time": []}}
        with patch.object(historical_service.httpx, "AsyncClient", FakeClient):
            await historical_service.get_historical_weather(28.6139, 77.2090, "2026-09-10", "2026-09-10")
            await historical_service.get_historical_weather(28.6139, 77.2090, "2026-09-10", "2026-09-10")
        self.assertEqual(FakeClient.calls, 1)

        FakeClient.calls = 0
        FakeClient.response_data = {"results": []}
        with patch.object(location_service.httpx, "AsyncClient", FakeClient):
            await location_service.search_location("Delhi")
            await location_service.search_location("  delhi  ")
        self.assertEqual(FakeClient.calls, 1)

    async def test_imd_cache_prevents_second_request(self):
        FakeClient.response_data = {"features": []}
        with patch.object(imd_cap_service.httpx, "AsyncClient", FakeClient):
            await imd_cap_service.get_imd_cap_notifications(50)
            await imd_cap_service.get_imd_cap_notifications(50)
        self.assertEqual(FakeClient.calls, 1)

    async def test_ingestion_coalesces_weather_write(self):
        location = {"name": "Delhi", "latitude": 28.6139, "longitude": 77.2090}
        raw = {"current": {"time": "2026-09-12T00:00"}}
        normalized = {"temperature_c": 25, "observed_at": "2026-09-12T00:00"}
        with (
            patch.object(realtime_ingestion_service, "fetch_open_meteo", AsyncMock(return_value=raw)) as fetch,
            patch.object(realtime_ingestion_service, "validate_open_meteo_data", return_value={"valid": True}),
            patch.object(realtime_ingestion_service, "normalize_open_meteo", return_value=normalized),
            patch.object(realtime_ingestion_service, "save_weather_record", AsyncMock()) as save,
        ):
            results = await asyncio.gather(*[
                realtime_ingestion_service.ingest_open_meteo_location(location)
                for _ in range(5)
            ])
        self.assertEqual(fetch.await_count, 1)
        self.assertEqual(save.await_count, 1)
        self.assertTrue(all(result == normalized for result in results))


class DuplicateAlertPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_existing_alert_does_not_write_again(self):
        existing = object()

        class Result:
            def scalar_one_or_none(self):
                return existing

        class Session:
            def __init__(self):
                self.add = AsyncMock()
                self.commit = AsyncMock()
                self.refresh = AsyncMock()

            async def execute(self, statement):
                return Result()

        class SessionFactory:
            async def __aenter__(self):
                self.session = Session()
                return self.session

            async def __aexit__(self, *args):
                return False

        with patch.object(database_service, "AsyncSessionLocal", return_value=SessionFactory()):
            returned = await database_service.save_official_alert({"identifier": "existing-alert"})
        self.assertIs(returned, existing)

    async def test_postgresql_persists_one_alert_for_duplicate_identifier(self):
        identifier = f"sprint11-test-{uuid4()}"
        alert = {"identifier": identifier, "event": "Sprint 11 test"}
        try:
            first = await database_service.save_official_alert(alert)
            second = await database_service.save_official_alert(alert)
            self.assertEqual(first.id, second.id)
        finally:
            async with AsyncSessionLocal() as session:
                await session.execute(
                    delete(OfficialAlert).where(OfficialAlert.identifier == identifier)
                )
                await session.commit()
            await close_db()


class LlmRoutingContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_tool_routing_contract_is_preserved(self):
        with patch.object(
            llm_service,
            "ask_llm",
            AsyncMock(return_value='{"tool": "forecast", "reason": "future weather"}'),
        ):
            result = await llm_service.choose_weather_tool("Will it rain tomorrow in Delhi?")
        self.assertEqual(result["tool"], "forecast")


class ApiRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_conversational_chat_skips_llm_routing(self):
        request = api.ChatRequest(message="Hello", session_id="sprint11-conversation")
        with (
            patch.object(api, "save_chat_message", AsyncMock()),
            patch.object(api, "understand_with_llm", AsyncMock()) as understand,
        ):
            response = await api.chat(request)
        self.assertEqual(response["tool"]["tool"], "conversation")
        understand.assert_not_awaited()

    async def test_cache_performance_endpoint_reports_metrics(self):
        response = await api.cache_performance_status()
        self.assertIn("hits", response)
        self.assertIn("misses", response)
        self.assertIn("coalesced_requests", response)


if __name__ == "__main__":
    unittest.main()
