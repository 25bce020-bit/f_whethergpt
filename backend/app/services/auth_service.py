"""Reusable password and server-side session helpers for optional authentication."""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import AuthSession, User

AUTH_COOKIE_NAME = "weathergpt_auth"
SESSION_LIFETIME_DAYS = int(os.getenv("AUTH_SESSION_LIFETIME_DAYS", "14"))
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def hash_password(password: str) -> str:
    """Hash passwords with stdlib scrypt, using a unique random salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N, _SCRYPT_R, _SCRYPT_P,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded:
        return False
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=base64.urlsafe_b64decode(salt),
            n=int(n), r=int(r), p=int(p),
        )
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError, UnicodeError):
        return False


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


async def create_auth_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    async with AsyncSessionLocal() as session:
        session.add(AuthSession(
            user_id=user_id,
            token_hash=_token_digest(token),
            expires_at=datetime.utcnow() + timedelta(days=SESSION_LIFETIME_DAYS),
        ))
        await session.commit()
    return token


async def get_user_for_token(token: str | None) -> User | None:
    if not token:
        return None
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AuthSession, User)
            .join(User, AuthSession.user_id == User.id)
            .where(AuthSession.token_hash == _token_digest(token))
        )
        pair = result.one_or_none()
        if pair is None:
            return None
        auth_session, user = pair
        if auth_session.expires_at <= datetime.utcnow():
            await session.delete(auth_session)
            await session.commit()
            return None
        return user


async def invalidate_auth_session(token: str | None) -> None:
    if not token:
        return
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(AuthSession).where(AuthSession.token_hash == _token_digest(token)))
        auth_session = result.scalar_one_or_none()
        if auth_session:
            await session.delete(auth_session)
            await session.commit()


async def get_optional_current_user(
    auth_token: str | None = Cookie(None, alias=AUTH_COOKIE_NAME),
) -> User | None:
    return await get_user_for_token(auth_token)


async def get_current_user(user: User | None = Depends(get_optional_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user
