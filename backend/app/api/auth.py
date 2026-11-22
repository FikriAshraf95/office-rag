"""Endpoints 16-17: password login and logout (SPEC-08 §3, SPEC-11 §5.2). Public: they run before sign-in."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.errors import ApiError
from app.api.schemas import LoginIn, MeOut
from app.config import Settings, get_settings
from app.security.identity import SESSION_COOKIE, login_identity, session_token
from app.security.limits import LoginLimiter
from app.security.passwords import DUMMY_HASH, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

SettingsDep = Annotated[Settings, Depends(get_settings)]
BAD_CREDENTIALS = "The username or password is wrong."


def _password_mode(settings: Settings) -> None:
    if settings.auth_mode != "password":
        raise ApiError(404, "not_found", "Password sign-in is off on this server.")


@router.post("/login", response_model=MeOut)
async def login(body: LoginIn, request: Request, response: Response, settings: SettingsDep) -> MeOut:
    _password_mode(settings)
    limiter: LoginLimiter = request.app.state.login_limiter
    username = body.username.strip().lower()
    limiter.check(username)
    user = settings.login_users_by_name.get(username)
    stored = user.password_hash.get_secret_value() if user else DUMMY_HASH
    if not verify_password(body.password, stored) or user is None:
        limiter.failed(username)
        raise ApiError(401, "bad_credentials", BAD_CREDENTIALS)
    limiter.succeeded(username)
    response.set_cookie(
        SESSION_COOKIE,
        session_token(username, user, settings),
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
    )
    me = login_identity(username, user)
    return MeOut(id=me.id, name=me.name, groups=list(me.groups), is_admin=me.is_admin)


@router.post("/logout", status_code=204)
async def logout(settings: SettingsDep) -> Response:
    _password_mode(settings)
    response = Response(status_code=204)
    response.delete_cookie(
        SESSION_COOKIE, httponly=True, secure=settings.app_env == "production", samesite="strict", path="/"
    )
    return response
