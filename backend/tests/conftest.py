"""Test host (SPEC-10 §2): real Postgres `rag_test`, per-test rollback, fake AI, network guard.

The network guard is configured in pyproject (`--disable-socket --allow-hosts=127.0.0.1,localhost,::1`).
"""

import atexit
import os
import shutil
import tempfile

TEST_API_KEY = "sk-test-never-log-this-4c1d9e"
ADMIN_URL = "postgresql://rag:rag@127.0.0.1:5433/rag"
TEST_DB = "rag_test"
TEST_DATABASE_URL = f"postgresql+asyncpg://rag:rag@127.0.0.1:5433/{TEST_DB}"
DEMO_USERS = (
    '{"aisyah":{"name":"Aisyah (HR)","groups":["all","hr"]},"ben":{"name":"Ben (Staff)","groups":["all"]}}'
)

STORAGE_DIR = tempfile.mkdtemp(prefix="rag-test-storage-")
atexit.register(shutil.rmtree, STORAGE_DIR, ignore_errors=True)

# Must be set before anything imports app.config.
os.environ.update(
    STORAGE_DIR=STORAGE_DIR,
    APP_ENV="test",
    AI_PROVIDER="fake",
    AUTH_MODE="demo",
    AI_API_KEY=TEST_API_KEY,
    DATABASE_URL=TEST_DATABASE_URL,
    DEMO_USERS=DEMO_USERS,
    RERANK_MODEL="",
)

import asyncio  # noqa: E402
import logging  # noqa: E402
from collections.abc import AsyncIterator, Callable, Iterator  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings  # noqa: E402
from app.db.engine import get_session  # noqa: E402
from app.main import create_app  # noqa: E402
from app.providers.registry import Providers, set_providers  # noqa: E402
from app.providers.usage import UsageRecorder  # noqa: E402
from tests.corpus import Corpus  # noqa: E402
from tests.dbutil import migrate, recreate_database  # noqa: E402

ALL_TABLES = "usage, questions, jobs, chunks, documents"


# --- Event loop: the selector loop on every platform. On Windows the default Proactor loop connects
# through ConnectEx, which bypasses pytest-socket's guard; the selector loop goes through socket.connect.


def pytest_asyncio_loop_factories(config: pytest.Config, item: pytest.Item) -> dict[str, object]:
    return {"selector": asyncio.SelectorEventLoop}


# --- Log capture for SPEC-09 §8 check 5: no log line of the whole run contains AI_API_KEY. ---


class _Collect(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


ALL_LOGS = _Collect()


def pytest_configure(config: pytest.Config) -> None:
    logging.getLogger().addHandler(ALL_LOGS)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    leaked = [line for line in ALL_LOGS.lines if TEST_API_KEY in line]
    if leaked:
        print(f"\nSPEC-09 ac05: AI_API_KEY appeared in {len(leaked)} log line(s).")
        session.exitstatus = 1


# --- Database ---


@pytest.fixture(scope="session", autouse=True)
def _database() -> None:
    recreate_database(TEST_DB)
    migrate(TEST_DATABASE_URL, "head")


@pytest.fixture(scope="session")
async def engine(_database: None) -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine(TEST_DATABASE_URL)
    yield eng
    await eng.dispose()


@pytest.fixture
async def connection(engine: AsyncEngine) -> AsyncIterator[AsyncConnection]:
    """One connection per test inside a transaction that is rolled back at the end."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        yield conn
        await trans.rollback()


@pytest.fixture
async def db(connection: AsyncConnection) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(bind=connection, join_transaction_mode="create_savepoint") as session:
        yield session


@pytest.fixture
async def committed_db(engine: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    """For tests that need real commits (worker, concurrency, NOTIFY); truncates afterwards."""
    yield engine
    async with engine.begin() as conn:
        await conn.exec_driver_sql(f"TRUNCATE {ALL_TABLES} RESTART IDENTITY CASCADE")


@pytest.fixture
async def sessions(connection: AsyncConnection) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Session factory on the test connection, for `process_one_job` (rolled back with the test)."""
    yield async_sessionmaker(connection, expire_on_commit=False, join_transaction_mode="create_savepoint")


# --- Providers and app ---


@pytest.fixture
def providers(connection: AsyncConnection) -> Iterator[Providers]:
    """Fake providers whose usage rows roll back with the test."""
    p = Providers(get_settings(), UsageRecorder(connection))
    set_providers(p)
    yield p
    set_providers(None)


@pytest.fixture
def app(db: AsyncSession, providers: Providers) -> FastAPI:
    application = create_app()

    async def _session() -> AsyncIterator[AsyncSession]:
        yield db

    application.dependency_overrides[get_session] = _session
    return application


def _client(app: FastAPI, user: str | None) -> httpx.AsyncClient:
    headers = {"X-Demo-User": user} if user else {}
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://test", headers=headers)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with _client(app, "ben") as c:
        yield c


@pytest.fixture
def client_as(app: FastAPI) -> Callable[[str | None], httpx.AsyncClient]:
    """`async with client_as("aisyah") as c:`; None sends no X-Demo-User."""
    return lambda user: _client(app, user)


@pytest.fixture
def corpus(
    client: httpx.AsyncClient,
    client_as: Callable[[str | None], httpx.AsyncClient],
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> Corpus:
    """Documents with chosen chunk texts, ingested through the real worker (see tests/corpus.py)."""
    return Corpus(client, client_as, sessions, providers, monkeypatch)
