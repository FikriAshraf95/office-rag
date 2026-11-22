"""Who is calling (SPEC-09 §3). Routes get the user only through `get_identity`."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

from app.api.errors import ApiError
from app.config import Settings, get_settings


@dataclass(frozen=True, slots=True)
class Identity:
    id: str
    name: str
    groups: tuple[str, ...]
    is_admin: bool


UNKNOWN_USER = "Choose a demo user: send the X-Demo-User header with one of the configured user ids."


def demo_identity(user_id: str | None, settings: Settings) -> Identity:
    user = settings.demo_users.get(user_id or "")
    if user_id is None or user is None:
        raise ApiError(401, "unknown_user", UNKNOWN_USER)
    # Every demo user is an admin; M100 changes who gets it.
    return Identity(id=user_id, name=user.name, groups=tuple(user.groups), is_admin=True)


async def get_identity(
    settings: Annotated[Settings, Depends(get_settings)],
    x_demo_user: Annotated[str | None, Header(alias="X-Demo-User")] = None,
) -> Identity:
    # AUTH_MODE=cloudflare_access arrives in M100; check_startup refuses it until then.
    return demo_identity(x_demo_user, settings)


CurrentUser = Annotated[Identity, Depends(get_identity)]
