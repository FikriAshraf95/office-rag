"""System endpoints 1-3 (SPEC-08 §3)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ConfigOut, DemoUserOut, HealthOut, MeOut
from app.config import ALLOWED_EXTENSIONS, DOC_TYPES, Settings, get_settings
from app.db.engine import get_session, ping
from app.security.identity import CurrentUser

router = APIRouter()

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health", response_model=HealthOut, responses={503: {"model": HealthOut}})
async def health(
    session: Annotated[AsyncSession, Depends(get_session)], settings: SettingsDep
) -> JSONResponse:
    db_ok = await ping(session)
    body = HealthOut(
        status="ok" if db_ok else "error", db="ok" if db_ok else "error", ai_provider=settings.ai_provider
    )
    return JSONResponse(body.model_dump(by_alias=True), status_code=200 if db_ok else 503)


@router.get("/api/v1/config", response_model=ConfigOut)
async def config(settings: SettingsDep) -> ConfigOut:
    demo_users = [] if settings.auth_mode != "demo" else settings.demo_users.items()
    return ConfigOut(
        allowed_extensions=ALLOWED_EXTENSIONS,
        max_upload_bytes=settings.max_upload_bytes,
        demo_users=[DemoUserOut(id=uid, name=u.name, groups=u.groups) for uid, u in demo_users],
        access_groups=settings.access_groups(),
        doc_types=DOC_TYPES,
        org_name=settings.org_name,
    )


@router.get("/api/v1/me", response_model=MeOut)
async def me(user: CurrentUser) -> MeOut:
    return MeOut(id=user.id, name=user.name, groups=list(user.groups))
