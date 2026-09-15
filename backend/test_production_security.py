"""Production-hardening regression coverage for operational routes and cookies."""

import asyncio
import secrets
import unittest
from http.cookies import SimpleCookie
from unittest.mock import patch

import httpx
from fastapi import HTTPException, Response

from app.database import close_db, init_db
from app.main import (
    SignupRequest,
    database_status,
    get_current_user,
    set_auth_cookie,
    signup,
)


class ProductionSecurityTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()

    async def asyncTearDown(self):
        await close_db()

    async def test_guest_cannot_access_operational_routes_but_root_is_public(self):
        from app.main import app

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            self.assertEqual((await client.get("/")).status_code, 200)
            for path in ("/database/status", "/database/summary", "/realtime/status", "/performance/cache"):
                self.assertEqual((await client.get(path)).status_code, 401)

    async def test_authenticated_session_can_access_operational_status(self):
        response = Response()
        email = f"production-security-{secrets.token_hex(8)}@example.test"
        await signup(SignupRequest(email=email, password="WeatherPass123"), response)
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])

        from app.main import app

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            client.cookies.set("weathergpt_auth", cookie["weathergpt_auth"].value)
            self.assertEqual((await client.get("/database/status")).status_code, 200)

    async def test_database_failure_returns_safe_message(self):
        class BrokenSession:
            async def __aenter__(self):
                raise RuntimeError("postgresql://private-user:private-password@internal-host/private-db")

            async def __aexit__(self, *_args):
                return False

        with patch("app.main.AsyncSessionLocal", return_value=BrokenSession()):
            with self.assertRaises(HTTPException) as error:
                await database_status(object())
        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "Database is unavailable.")
        self.assertNotIn("private-password", error.exception.detail)

    def test_cookie_is_httponly_and_secure_settings_are_preserved(self):
        response = Response()
        set_auth_cookie(response, "opaque-token")
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        self.assertTrue(cookie["weathergpt_auth"]["httponly"])
        self.assertEqual(cookie["weathergpt_auth"]["path"], "/")

    async def test_current_user_dependency_rejects_guest(self):
        with self.assertRaises(HTTPException) as error:
            await get_current_user(None)
        self.assertEqual(error.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
