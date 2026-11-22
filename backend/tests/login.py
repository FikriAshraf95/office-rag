"""Password-login test host (SPEC-11 §6 checks 5-8): three login users and an app in `password` mode.

`login_client(user)` signs in through `POST /api/v1/auth/login` and keeps the session cookie.
"""

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import LoginUser, get_settings
from app.db.engine import get_session
from app.main import create_app
from app.security.passwords import hash_password

ADMIN = "aisyah"
STAFF = "ben"
OTHER = "chong"
PASSWORDS = {ADMIN: "aisyah-pass-123", STAFF: "ben-pass-4567", OTHER: "chong-pass-89"}
SESSION_SECRET = "test-session-secret-0123456789abcdef-xyz"
# Hashed once: scrypt is deliberately slow.
LOGIN_USERS = {
    ADMIN: LoginUser(
        name="Aisyah (HR)",
        groups=["all", "hr"],
        admin=True,
        password_hash=SecretStr(hash_password(PASSWORDS[ADMIN])),
    ),
    STAFF: LoginUser(
        name="Ben (Staff)", groups=["all"], password_hash=SecretStr(hash_password(PASSWORDS[STAFF]))
    ),
    "Chong": LoginUser(
        name="Chong (Finance)",
        groups=["all", "finance"],
        password_hash=SecretStr(hash_password(PASSWORDS[OTHER])),
    ),
}


@pytest.fixture
def login_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    for name, value in {
        "auth_mode": "password",
        "login_users": LOGIN_USERS,
        "session_secret": SecretStr(SESSION_SECRET),
        "session_days": 7,
        "chat_rate_per_min": 6,
        "chat_daily_cap": 100,
    }.items():
        monkeypatch.setattr(settings, name, value)


@pytest.fixture
def login_app(login_settings: None, db: AsyncSession, providers: object) -> FastAPI:
    application = create_app()

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[get_session] = _session
    return application


def anonymous(app: FastAPI, headers: dict[str, str] | None = None) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers or {})


LoginClient = Callable[..., AbstractAsyncContextManager[httpx.AsyncClient]]


@pytest.fixture
def login_client(login_app: FastAPI) -> LoginClient:
    """`async with login_client(STAFF) as c:` is a client signed in as that user; None stays signed out."""

    @asynccontextmanager
    async def make(
        user: str | None = STAFF, headers: dict[str, str] | None = None
    ) -> AsyncIterator[httpx.AsyncClient]:
        async with anonymous(login_app, headers) as client:
            if user is not None:
                resp = await client.post(
                    "/api/v1/auth/login", json={"username": user, "password": PASSWORDS[user]}
                )
                assert resp.status_code == 200, resp.text
            yield client

    return make
