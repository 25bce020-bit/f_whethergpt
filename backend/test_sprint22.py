"""Sprint 22 authentication and guest/authenticated chat coverage."""

import asyncio
import secrets
import unittest
from http.cookies import SimpleCookie

from fastapi import HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import select

from app.database import AsyncSessionLocal, close_db, init_db
from app.main import (
    ChatRequest,
    LoginRequest,
    SignupRequest,
    auth_me,
    login,
    logout,
    process_chat_message,
    signup,
)
from app.models import Conversation, User
from app.services.auth_service import get_user_for_token, verify_password
from app.services.mode_service import WeatherMode, resolve_mode


class Sprint22AuthenticationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()
        self.email = f"sprint22-{secrets.token_hex(8)}@example.test"
        self.password = "WeatherPass123"

    async def asyncTearDown(self):
        await close_db()

    @staticmethod
    def cookie_token(response: Response) -> str:
        cookie = SimpleCookie()
        cookie.load(response.headers["set-cookie"])
        return cookie["weathergpt_auth"].value

    async def create_account(self):
        response = Response()
        payload = await signup(
            SignupRequest(name="Sprint 22", email=self.email, password=self.password), response
        )
        return payload, self.cookie_token(response)

    async def test_signup_password_hash_and_public_shape(self):
        payload, _ = await self.create_account()
        self.assertEqual(payload["user"]["email"], self.email)
        self.assertNotIn("password_hash", payload["user"])
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.email == self.email))).scalar_one()
        self.assertNotEqual(user.password_hash, self.password)
        self.assertTrue(user.password_hash.startswith("scrypt$"))
        self.assertTrue(verify_password(self.password, user.password_hash))

    async def test_duplicate_invalid_signup_and_invalid_login(self):
        await self.create_account()
        with self.assertRaises(HTTPException) as duplicate:
            await signup(SignupRequest(email=self.email, password=self.password), Response())
        self.assertEqual(duplicate.exception.status_code, 409)
        with self.assertRaises(ValidationError):
            SignupRequest(email="not-an-email", password="short")
        with self.assertRaises(HTTPException) as invalid_login:
            await login(LoginRequest(email=self.email, password="WrongPassword123"), Response())
        self.assertEqual(invalid_login.exception.status_code, 401)

    async def test_login_me_and_logout(self):
        await self.create_account()
        response = Response()
        payload = await login(LoginRequest(email=self.email, password=self.password), response)
        token = self.cookie_token(response)
        user = await get_user_for_token(token)
        self.assertEqual(payload["user"]["id"], user.id)
        self.assertEqual((await auth_me(user))["user"]["email"], self.email)
        with self.assertRaises(HTTPException) as guest_me:
            await auth_me(None)
        self.assertEqual(guest_me.exception.status_code, 401)
        logout_response = Response()
        self.assertEqual((await logout(logout_response, token))["message"], "Logged out.")
        self.assertIsNone(await get_user_for_token(token))

    async def test_guest_and_authenticated_chat_ownership_and_session_echo(self):
        guest_id = f"guest-s22-{secrets.token_hex(8)}"
        guest_result = await process_chat_message(ChatRequest(message="Hi", session_id=guest_id))
        self.assertEqual(guest_result["session_id"], guest_id)
        async with AsyncSessionLocal() as session:
            guest_conversation = (await session.execute(
                select(Conversation).where(Conversation.session_id == guest_id)
            )).scalar_one()
        self.assertIsNone(guest_conversation.user_id)

        account, _ = await self.create_account()
        async with AsyncSessionLocal() as session:
            user = await session.get(User, account["user"]["id"])
        authenticated_result = await process_chat_message(
            ChatRequest(message="Hello", session_id=guest_id), user
        )
        self.assertEqual(authenticated_result["session_id"], guest_id)
        async with AsyncSessionLocal() as session:
            conversation = (await session.execute(
                select(Conversation).where(Conversation.session_id == guest_id)
            )).scalar_one()
        self.assertEqual(conversation.user_id, user.id)

    async def test_existing_mode_routing_regressions(self):
        self.assertEqual(resolve_mode("Should I irrigate wheat tomorrow?", "normal").active_mode, WeatherMode.FARMER)
        self.assertEqual(resolve_mode("Compare GFS and Open-Meteo.", "normal").active_mode, WeatherMode.RESEARCHER)
        self.assertEqual(resolve_mode("Should I travel to Goa tomorrow?", "normal").active_mode, WeatherMode.TRAVELLER)


if __name__ == "__main__":
    unittest.main()
