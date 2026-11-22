"""Async engine and the per-request session dependency."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    # hide_parameters: a database error logged with its traceback must not carry chunk text (SPEC-09 §5).
    return create_async_engine(get_settings().database_url, pool_pre_ping=True, hide_parameters=True)


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_sessionmaker()() as session:
        yield session


async def ping(session: AsyncSession) -> bool:
    """True when the database answers a trivial query."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        return False
    return True
