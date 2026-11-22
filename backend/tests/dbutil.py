"""Create databases and run Alembic from tests. Both run in a fresh thread with its own event loop."""

import asyncio
import threading
from collections.abc import Callable
from pathlib import Path

import asyncpg
from alembic.config import Config

from alembic import command

ADMIN_DSN = "postgresql://rag:rag@127.0.0.1:5433/rag"
BACKEND = Path(__file__).resolve().parent.parent


def _in_thread(fn: Callable[[], None]) -> None:
    errors: list[BaseException] = []

    def target() -> None:
        try:
            fn()
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    if errors:
        raise errors[0]


def recreate_database(name: str) -> None:
    async def run() -> None:
        conn = await asyncpg.connect(ADMIN_DSN)
        try:
            await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            await conn.execute(f'CREATE DATABASE "{name}"')
        finally:
            await conn.close()

    _in_thread(lambda: asyncio.run(run()))


def alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def migrate(url: str, revision: str) -> None:
    _in_thread(lambda: command.upgrade(alembic_config(url), revision))


def downgrade(url: str, revision: str) -> None:
    _in_thread(lambda: command.downgrade(alembic_config(url), revision))
