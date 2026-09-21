import pytest

from app.services.google_routes_service import GoogleRoutesError, _normalize_route, compute_routes


def test_normalize_route():
    route = _normalize_route(
        {
            "distanceMeters": 525400,
            "duration": "650s",
            "polyline": {"encodedPolyline": "abc"},
        },
        0,
    )
    assert route["route_index"] == 0
    assert route["distance_km"] == 525.4
    assert route["duration_minutes"] == pytest.approx(10.833, rel=1e-3)
    assert route["polyline"] == "abc"


@pytest.mark.asyncio
async def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_ROUTES_API_KEY", raising=False)
    with pytest.raises(GoogleRoutesError, match="not configured"):
        await compute_routes(
            origin_latitude=23.0225,
            origin_longitude=72.5714,
            destination_latitude=19.0760,
            destination_longitude=72.8777,
        )


@pytest.mark.asyncio
async def test_compute_routes_normalizes_google_payload(monkeypatch):
    monkeypatch.setenv("GOOGLE_ROUTES_API_KEY", "test-key")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "routes": [
                    {
                        "distanceMeters": 525400,
                        "duration": "6500s",
                        "polyline": {"encodedPolyline": "primary"},
                    },
                    {
                        "distanceMeters": 548200,
                        "duration": "6700s",
                        "polyline": {"encodedPolyline": "alternative"},
                    },
                ]
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            assert url.endswith("directions/v2:computeRoutes")
            assert kwargs["headers"]["X-Goog-Api-Key"] == "test-key"
            assert kwargs["headers"]["X-Goog-FieldMask"].startswith("routes.")
            assert kwargs["json"]["computeAlternativeRoutes"] is True
            return FakeResponse()

    import app.services.google_routes_service as module

    monkeypatch.setattr(module.httpx, "AsyncClient", FakeClient)
    result = await module.compute_routes(
        origin_latitude=23.0225,
        origin_longitude=72.5714,
        destination_latitude=19.0760,
        destination_longitude=72.8777,
    )
    assert len(result["routes"]) == 2
    assert result["routes"][0]["polyline"] == "primary"
    assert result["routes"][1]["polyline"] == "alternative"
