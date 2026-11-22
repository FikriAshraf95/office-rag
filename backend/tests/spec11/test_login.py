"""SPEC-11 §6 checks 5-8 (M100): password login, sessions, admin-only routes, limits and guards."""

import time
import uuid
from typing import Any

import httpx
import jwt
import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from app.config import LoginUser, Settings, StartupError, check_startup, get_settings
from app.security.identity import SESSION_COOKIE
from app.security.limits import ChatLimiter, LoginLimiter
from app.security.passwords import hash_password, main, verify_password
from tests.login import ADMIN, LOGIN_USERS, OTHER, PASSWORDS, SESSION_SECRET, STAFF, LoginClient, anonymous
from tests.uploads import markdown, upload


def assert_problem(resp: httpx.Response, status: int, code: str) -> dict[str, Any]:
    assert resp.status_code == status, resp.text
    assert resp.headers["content-type"].startswith("application/problem+json")
    body: dict[str, Any] = resp.json()
    assert body["code"] == code
    return body


async def _login(client: httpx.AsyncClient, username: str, password: str) -> httpx.Response:
    return await client.post("/api/v1/auth/login", json={"username": username, "password": password})


# --- Passwords ---


def test_spec11_m100_password_hash_round_trip() -> None:
    stored = hash_password("correct horse")
    assert stored.startswith("scrypt:") and "$" not in stored  # Compose would interpolate a `$`
    assert verify_password("correct horse", stored)
    assert not verify_password("wrong horse", stored)
    assert hash_password("correct horse") != stored  # salted
    for broken in ("", "scrypt:x", "bcrypt:1:2:3:4:5", "scrypt:16384:8:1:!!:!!"):
        assert not verify_password("correct horse", broken)


def test_spec11_m100_hash_command(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    assert main(["--secret"]) == 0
    assert len(capsys.readouterr().out.strip()) >= 32
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO("a-good-password\n"))
    assert main([]) == 0
    assert verify_password("a-good-password", capsys.readouterr().out.strip())


# --- Check 5: only a valid session gets in ---


async def test_spec11_ac05_login_sets_a_safe_session_cookie(login_app: FastAPI) -> None:
    async with anonymous(login_app) as c:
        resp = await _login(c, "  Ben ", PASSWORDS[STAFF])  # usernames ignore case and spaces
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"id": STAFF, "name": "Ben (Staff)", "groups": ["all"], "isAdmin": False}
        cookie = resp.headers["set-cookie"].lower()
        assert cookie.startswith(f"{SESSION_COOKIE}=")
        assert "httponly" in cookie and "samesite=strict" in cookie and "path=/" in cookie
        assert PASSWORDS[STAFF] not in resp.headers["set-cookie"]
        assert (await c.get("/api/v1/me")).json()["id"] == STAFF

        assert (await c.post("/api/v1/auth/logout")).status_code == 204
        assert_problem(await c.get("/api/v1/me"), 401, "unknown_user")


async def test_spec11_ac05_cookie_is_secure_in_production(
    login_app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "app_env", "production")
    async with anonymous(login_app) as c:
        resp = await _login(c, STAFF, PASSWORDS[STAFF])
    assert "secure" in resp.headers["set-cookie"].lower()


async def test_spec11_ac05_wrong_password_or_user_is_401(login_app: FastAPI) -> None:
    async with anonymous(login_app) as c:
        wrong = assert_problem(await _login(c, STAFF, "not-his-password"), 401, "bad_credentials")
        unknown = assert_problem(await _login(c, "mallory", PASSWORDS[STAFF]), 401, "bad_credentials")
        assert wrong["detail"] == unknown["detail"]  # doesn't say which part was wrong
        assert "set-cookie" not in (await _login(c, STAFF, "nope")).headers
        assert_problem(await c.get("/api/v1/me"), 401, "unknown_user")


def _forged(**overrides: Any) -> str:
    now = int(time.time())
    claims = {"sub": STAFF, "iat": now, "exp": now + 600, "pwd": "0" * 16, **overrides}
    secret = overrides.pop("secret", SESSION_SECRET)
    claims.pop("secret", None)
    return jwt.encode(claims, secret, algorithm="HS256")


@pytest.mark.parametrize(
    "cookie",
    [
        "garbage",
        _forged(secret="someone-elses-secret-0123456789abcdef"),
        _forged(exp=int(time.time()) - 10),
        _forged(),  # right secret, wrong password stamp
        jwt.encode({"sub": STAFF, "exp": int(time.time()) + 600}, "x" * 40, algorithm="HS256"),
    ],
    ids=["garbage", "wrong-secret", "expired", "wrong-stamp", "no-stamp"],
)
async def test_spec11_ac05_bad_session_cookie_is_401(login_app: FastAPI, cookie: str) -> None:
    async with anonymous(login_app) as c:
        c.cookies.set(SESSION_COOKIE, cookie)
        for path in ("/api/v1/me", "/api/v1/documents"):
            assert_problem(await c.get(path), 401, "unknown_user")


async def test_spec11_ac05_password_change_ends_old_sessions(
    login_client: LoginClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async with login_client(STAFF) as c:
        assert (await c.get("/api/v1/me")).status_code == 200
        changed = {
            **LOGIN_USERS,
            STAFF: LoginUser(
                name="Ben (Staff)", groups=["all"], password_hash=SecretStr(hash_password("new-pass-99"))
            ),
        }
        monkeypatch.setattr(get_settings(), "login_users", changed)
        assert_problem(await c.get("/api/v1/me"), 401, "unknown_user")


async def test_spec11_ac05_config_in_password_mode(login_app: FastAPI) -> None:
    async with anonymous(login_app) as c:
        config = (await c.get("/api/v1/config")).json()
    assert config["authMode"] == "password"
    assert config["demoUsers"] == []
    assert config["accessGroups"] == ["all", "finance", "hr"]


async def test_spec11_m100_login_routes_are_off_in_demo_mode(client: httpx.AsyncClient) -> None:
    assert_problem(await _login(client, STAFF, PASSWORDS[STAFF]), 404, "not_found")
    assert_problem(await client.post("/api/v1/auth/logout"), 404, "not_found")


# --- Check 6: X-Demo-User has no effect ---


async def test_spec11_ac06_demo_header_is_ignored(login_client: LoginClient) -> None:
    async with login_client(None, headers={"X-Demo-User": "aisyah"}) as c:
        assert_problem(await c.get("/api/v1/me"), 401, "unknown_user")
    async with login_client(STAFF, headers={"X-Demo-User": "aisyah"}) as c:
        me = (await c.get("/api/v1/me")).json()
    assert me["id"] == STAFF and me["isAdmin"] is False


# --- Check 7: admin-only routes and limits ---


async def test_spec11_ac07_non_admin_gets_403_on_admin_routes(login_client: LoginClient) -> None:
    async with login_client(ADMIN) as admin:
        created = await upload(admin, markdown("m100"), "policy.md", title="Policy")
        assert created.status_code == 202, created.text
        doc_id = created.json()["id"]
        assert (await admin.get("/api/v1/usage/summary")).status_code == 200

    async with login_client(STAFF) as staff:
        assert (await staff.get(f"/api/v1/documents/{doc_id}")).status_code == 200  # can still read
        calls: list[tuple[str, str, dict[str, Any]]] = [
            ("POST", "/api/v1/documents", {"files": {"file": ("x.md", markdown("x"))}}),
            ("POST", f"/api/v1/documents/{doc_id}/file", {"files": {"file": ("x.md", markdown("y"))}}),
            ("PATCH", f"/api/v1/documents/{doc_id}", {"json": {"title": "Mine"}}),
            ("DELETE", f"/api/v1/documents/{doc_id}", {}),
            ("POST", f"/api/v1/documents/{doc_id}/reingest", {}),
            ("GET", "/api/v1/usage/summary", {}),
        ]
        for method, path, kwargs in calls:
            assert_problem(await staff.request(method, path, **kwargs), 403, "admin_only")
        # An unknown id gives the same answer, so a non-admin learns nothing about which ids exist.
        assert_problem(await staff.delete(f"/api/v1/documents/{uuid.uuid4()}"), 403, "admin_only")


async def test_spec11_ac07_seventh_question_in_a_minute_is_429(login_client: LoginClient) -> None:
    async with login_client(STAFF) as staff, login_client(OTHER) as other:
        for i in range(6):
            resp = await staff.post("/api/v1/chat", json={"question": f"Question {i}?"})
            assert resp.status_code == 200, resp.text
        resp = await staff.post("/api/v1/chat", json={"question": "One more?"})
        body = assert_problem(resp, 429, "user_rate_limited")
        assert "faster" in body["detail"]
        assert int(resp.headers["retry-after"]) >= 1
        # Limits are per user.
        assert (await other.post("/api/v1/chat", json={"question": "Mine?"})).status_code == 200


async def test_spec11_ac07_daily_cap_is_429(
    login_client: LoginClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "chat_daily_cap", 2)
    async with login_client(STAFF) as staff:
        for i in range(2):
            assert (await staff.post("/api/v1/chat", json={"question": f"Q{i}?"})).status_code == 200
        resp = await staff.post("/api/v1/chat", json={"question": "Third?"})
    body = assert_problem(resp, 429, "user_rate_limited")
    assert "today" in body["detail"]


async def test_spec11_ac07_too_many_failed_logins_is_429(login_app: FastAPI) -> None:
    async with anonymous(login_app) as c:
        for _ in range(10):
            assert_problem(await _login(c, STAFF, "guess"), 401, "bad_credentials")
        # Locked even with the right password, until the window passes.
        body = assert_problem(await _login(c, STAFF, PASSWORDS[STAFF]), 429, "user_rate_limited")
        assert "sign-ins" in body["detail"]
        # Other usernames are not affected.
        assert (await _login(c, ADMIN, PASSWORDS[ADMIN])).status_code == 200


def test_spec11_ac07_login_limiter_window() -> None:
    now = [0.0]
    limiter = LoginLimiter(max_failures=2, window=900, clock=lambda: now[0])
    limiter.failed("u")
    limiter.failed("u")
    with pytest.raises(Exception, match="sign-ins"):
        limiter.check("u")
    now[0] += 900
    limiter.check("u")
    limiter.failed("u")
    limiter.succeeded("u")
    limiter.check("u")


def test_spec11_ac07_bucket_refills_over_time() -> None:
    now = [0.0]
    limiter = ChatLimiter(6, clock=lambda: now[0])
    assert all(limiter.take("u") is None for _ in range(6))
    wait = limiter.take("u")
    assert wait is not None and 9 < wait <= 10
    now[0] += 10
    assert limiter.take("u") is None
    assert limiter.take("u") is not None


async def test_spec11_ac07_limits_off_in_demo_mode(client: httpx.AsyncClient) -> None:
    for i in range(8):
        assert (await client.post("/api/v1/chat", json={"question": f"Demo {i}?"})).status_code == 200


# --- Check 8: startup guards ---


def _password(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "ai_api_key": "k",
        "app_env": "production",
        "ai_provider": "ilmu",
        "auth_mode": "password",
        "login_users": LOGIN_USERS,
        "session_secret": SESSION_SECRET,
    }
    return Settings(_env_file=None, **{**base, **overrides})


def test_spec11_ac08_production_refuses_demo_identity() -> None:
    with pytest.raises(StartupError, match="Demo identity is not allowed"):
        check_startup(_password(auth_mode="demo"))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"login_users": {}}, "LOGIN_USERS"),
        ({"session_secret": ""}, "SESSION_SECRET"),
        ({"session_secret": "too-short"}, "SESSION_SECRET"),
        (
            {"login_users": {"x": LoginUser(name="X", groups=["all"], password_hash=SecretStr("hunter2"))}},
            "passwordHash",
        ),
    ],
)
def test_spec11_ac08_password_mode_needs_its_settings(overrides: dict[str, Any], message: str) -> None:
    with pytest.raises(StartupError, match=message):
        check_startup(_password(**overrides))


def test_spec11_ac08_production_with_password_login_starts() -> None:
    check_startup(_password())


def test_spec11_m100_login_users_parse_from_env_json(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = '{"Fikri":{"name":"Fikri","groups":["all","hr"],"admin":true,"passwordHash":"scrypt:1:2:3:a:b"}}'
    monkeypatch.setenv("LOGIN_USERS", raw)
    s = Settings(_env_file=None)
    user = s.login_users_by_name["fikri"]
    assert user.admin and user.groups == ["all", "hr"]
    assert "scrypt:1:2:3" not in repr(s)
