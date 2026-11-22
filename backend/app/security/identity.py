"""Who is calling (SPEC-09 §3, SPEC-11 §5.2). Routes get the user only through `get_identity`.

`AUTH_MODE=demo` reads `X-Demo-User`. `AUTH_MODE=password` reads the signed session cookie set by
`POST /api/v1/auth/login` and ignores `X-Demo-User`.
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header

from app.api.errors import ApiError
from app.config import LoginUser, Settings, get_settings


@dataclass(frozen=True, slots=True)
class Identity:
    id: str
    name: str
    groups: tuple[str, ...]
    is_admin: bool


UNKNOWN_USER = "Choose a demo user: send the X-Demo-User header with one of the configured user ids."
NOT_SIGNED_IN = "You're not signed in, or your session has expired. Sign in again."
ADMIN_ONLY = "Only admins can do this. You can still ask questions and read documents."

SESSION_COOKIE = "rag_session"
SESSION_ALGORITHM = "HS256"


def demo_identity(user_id: str | None, settings: Settings) -> Identity:
    user = settings.demo_users.get(user_id or "")
    if user_id is None or user is None:
        raise ApiError(401, "unknown_user", UNKNOWN_USER)
    # Every demo user is an admin; the admin role matters only in password mode.
    return Identity(id=user_id, name=user.name, groups=tuple(user.groups), is_admin=True)


def login_identity(username: str, user: LoginUser) -> Identity:
    return Identity(id=username, name=user.name, groups=tuple(user.groups), is_admin=user.admin)


def _password_stamp(user: LoginUser) -> str:
    """Changes with the password hash, so a new password ends every older session."""
    return hashlib.sha256(user.password_hash.get_secret_value().encode()).hexdigest()[:16]


def session_token(username: str, user: LoginUser, settings: Settings) -> str:
    now = int(time.time())
    claims = {
        "sub": username,
        "iat": now,
        "exp": now + settings.session_days * 86400,
        "pwd": _password_stamp(user),
    }
    return jwt.encode(claims, settings.session_secret.get_secret_value(), algorithm=SESSION_ALGORITHM)


def session_identity(token: str | None, settings: Settings) -> Identity:
    if not token:
        raise ApiError(401, "unknown_user", NOT_SIGNED_IN)
    try:
        claims = jwt.decode(
            token,
            settings.session_secret.get_secret_value(),
            algorithms=[SESSION_ALGORITHM],
            options={"require": ["sub", "exp", "pwd"]},
        )
    except jwt.InvalidTokenError as exc:
        raise ApiError(401, "unknown_user", NOT_SIGNED_IN) from exc
    username = str(claims["sub"])
    user = settings.login_users_by_name.get(username)
    if user is None or claims["pwd"] != _password_stamp(user):  # removed user, or password changed
        raise ApiError(401, "unknown_user", NOT_SIGNED_IN)
    return login_identity(username, user)


async def get_identity(
    settings: Annotated[Settings, Depends(get_settings)],
    x_demo_user: Annotated[str | None, Header(alias="X-Demo-User")] = None,
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE, include_in_schema=False)] = None,
) -> Identity:
    if settings.auth_mode == "password":
        return session_identity(session, settings)
    return demo_identity(x_demo_user, settings)


CurrentUser = Annotated[Identity, Depends(get_identity)]


async def require_admin(user: CurrentUser) -> Identity:
    """Upload, replace, patch, delete, re-ingest and usage are admin-only (SPEC-11 §5.3)."""
    if not user.is_admin:
        raise ApiError(403, "admin_only", ADMIN_ONLY)
    return user


AdminUser = Annotated[Identity, Depends(require_admin)]
