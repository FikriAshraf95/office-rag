"""Invariant: the private marker is never visible to a non-member (SPEC-09 §4).

M01: the fixture is uploaded for real as `{hr}` and every document read path is checked for `ben`
(documents list, get, file, a duplicate upload). M02 adds chunks and re-ingest; M03 search;
M04 chat events and `questions` rows.
"""

import json
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.db.models import Question
from app.ingestion import extract as extraction
from app.ingestion.chunking import WhitespaceCounter
from app.ingestion.types import ChunkDraft, DocMeta, IngestResult
from app.ingestion.worker import process_one_job
from app.providers.registry import Providers
from tests.helpers import PRIVATE_MARKER
from tests.login import ADMIN as LOGIN_ADMIN
from tests.login import STAFF as LOGIN_STAFF
from tests.login import LoginClient
from tests.uploads import upload

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "private_salary_bands.md"
READ_PATHS = ["/health", "/api/v1/config", "/api/v1/me", "/api/v1/documents"]


def test_private_fixture_contains_marker() -> None:
    assert PRIVATE_MARKER in FIXTURE.read_text(encoding="utf-8")


async def test_private_marker_absent_for_ben_on_every_read_path(
    client: httpx.AsyncClient, client_as: Callable[[str | None], httpx.AsyncClient]
) -> None:
    async with client_as("aisyah") as aisyah:
        resp = await upload(
            aisyah, FIXTURE.read_bytes(), "private_salary_bands.md", title="Salary bands", accessGroups=["hr"]
        )
        assert resp.status_code == 202, resp.text
        doc_id = resp.json()["id"]
        # Sanity: the member can read it, so a clean result for Ben means the filter works.
        assert PRIVATE_MARKER in (await aisyah.get(f"/api/v1/documents/{doc_id}/file")).text

    for path in [*READ_PATHS, f"/api/v1/documents/{doc_id}", f"/api/v1/documents/{doc_id}/file"]:
        resp = await client.get(path)
        assert PRIVATE_MARKER not in resp.text, path
        assert "Salary bands" not in resp.text, path

    duplicate = await upload(client, FIXTURE.read_bytes(), "copy.md")
    assert duplicate.status_code == 409
    assert PRIVATE_MARKER not in duplicate.text
    assert "existingId" not in duplicate.json()


async def test_private_marker_absent_for_ben_on_chunk_and_reingest_paths(
    client: httpx.AsyncClient,
    client_as: Callable[[str | None], httpx.AsyncClient],
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M02: the document's chunks carry the marker text; only a member may list them or re-ingest."""
    marker_text = FIXTURE.read_text(encoding="utf-8")

    def extract_marker(*_: Any, **__: Any) -> IngestResult:
        chunk = ChunkDraft("text", marker_text, ["Salary bands"], 10)
        return IngestResult([chunk], DocMeta(language="en"))

    monkeypatch.setattr(extraction, "extract", extract_marker)
    async with client_as("aisyah") as aisyah:
        resp = await upload(
            aisyah, FIXTURE.read_bytes(), "private_salary_bands.md", title="Salary bands", accessGroups=["hr"]
        )
        doc_id = resp.json()["id"]
        await process_one_job(sessions, get_settings(), providers, WhitespaceCounter(), "w")
        chunks = await aisyah.get(f"/api/v1/documents/{doc_id}/chunks")
        assert PRIVATE_MARKER in chunks.text  # sanity: the member sees it

    for method, path in [
        ("GET", f"/api/v1/documents/{doc_id}/chunks"),
        ("GET", f"/api/v1/documents/{doc_id}/chunks?around={uuid.uuid4()}"),
        ("POST", f"/api/v1/documents/{doc_id}/reingest"),
    ]:
        resp = await client.request(method, path)
        assert resp.status_code == 404, path
        assert PRIVATE_MARKER not in resp.text, path
        assert "Salary bands" not in resp.text, path


async def test_private_marker_absent_for_ben_on_search(
    client: httpx.AsyncClient,
    client_as: Callable[[str | None], httpx.AsyncClient],
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M03: /search with the marker text itself, as a non-member, returns neither marker nor title."""
    marker_text = FIXTURE.read_text(encoding="utf-8")

    def extract_marker(*_: Any, **__: Any) -> IngestResult:
        return IngestResult([ChunkDraft("text", marker_text, ["Salary bands"], 10)], DocMeta(language="en"))

    monkeypatch.setattr(extraction, "extract", extract_marker)
    async with client_as("aisyah") as aisyah:
        await upload(
            aisyah, FIXTURE.read_bytes(), "private_salary_bands.md", title="Salary bands", accessGroups=["hr"]
        )
        await process_one_job(sessions, get_settings(), providers, WhitespaceCounter(), "w")
        member = await aisyah.post("/api/v1/search", json={"query": PRIVATE_MARKER})
        assert PRIVATE_MARKER in member.text  # sanity: the member finds it

    for query in [PRIVATE_MARKER, marker_text[:500], "salary bands"]:
        resp = await client.post("/api/v1/search", json={"query": query})
        assert resp.status_code == 200
        assert PRIVATE_MARKER not in resp.text, query
        assert "Salary bands" not in resp.text, query


async def test_private_marker_absent_for_ben_on_chat_and_question_rows(
    client: httpx.AsyncClient,
    client_as: Callable[[str | None], httpx.AsyncClient],
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M04: every /chat event and every `questions` row written for ben is free of the marker and title."""
    marker_text = FIXTURE.read_text(encoding="utf-8")

    def extract_marker(*_: Any, **__: Any) -> IngestResult:
        return IngestResult([ChunkDraft("text", marker_text, ["Salary bands"], 10)], DocMeta(language="en"))

    monkeypatch.setattr(extraction, "extract", extract_marker)
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)  # nothing may pass for ben, even ungated
    async with client_as("aisyah") as aisyah:
        await upload(
            aisyah, FIXTURE.read_bytes(), "private_salary_bands.md", title="Salary bands", accessGroups=["hr"]
        )
        await process_one_job(sessions, get_settings(), providers, WhitespaceCounter(), "w")
        member = await aisyah.post("/api/v1/chat", json={"question": "What are the salary bands?"})
        assert PRIVATE_MARKER in member.text  # sanity: the member's answer quotes it

    for question in ["What are the salary bands?", marker_text[:500], PRIVATE_MARKER]:
        resp = await client.post("/api/v1/chat", json={"question": question})
        assert resp.status_code == 200
        events = resp.text
        assert PRIVATE_MARKER not in events, question
        assert "Salary bands" not in events, question

    rows = (await db.execute(select(Question).where(Question.user_id == "ben"))).scalars().all()
    assert len(rows) == 3
    for row in rows:  # `question` is left out: it holds what ben typed, which may be the marker itself
        await db.refresh(row)
        written = json.dumps([row.answer, row.sources, row.model, row.error_code])
        assert PRIVATE_MARKER not in written
        assert "Salary bands" not in written


async def test_private_marker_absent_for_non_member_login_user(
    login_client: LoginClient,
    sessions: async_sessionmaker[AsyncSession],
    providers: Providers,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M100: in `password` mode a signed-in non-member (and a demo header naming a member)
    sees neither marker nor title on documents, search or chat."""
    marker_text = FIXTURE.read_text(encoding="utf-8")

    def extract_marker(*_: Any, **__: Any) -> IngestResult:
        return IngestResult([ChunkDraft("text", marker_text, ["Salary bands"], 10)], DocMeta(language="en"))

    monkeypatch.setattr(extraction, "extract", extract_marker)
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)
    async with login_client(LOGIN_ADMIN) as admin:
        resp = await upload(
            admin, FIXTURE.read_bytes(), "private_salary_bands.md", title="Salary bands", accessGroups=["hr"]
        )
        assert resp.status_code == 202, resp.text
        doc_id = resp.json()["id"]
        await process_one_job(sessions, get_settings(), providers, WhitespaceCounter(), "w")
        member = await admin.post("/api/v1/search", json={"query": PRIVATE_MARKER})
        assert PRIVATE_MARKER in member.text  # sanity: the member finds it

    async with login_client(LOGIN_STAFF, headers={"X-Demo-User": "aisyah"}) as staff:
        responses = [
            await staff.get("/api/v1/documents"),
            await staff.get(f"/api/v1/documents/{doc_id}"),
            await staff.get(f"/api/v1/documents/{doc_id}/file"),
            await staff.get(f"/api/v1/documents/{doc_id}/chunks"),
            await staff.post("/api/v1/search", json={"query": PRIVATE_MARKER}),
            await staff.post("/api/v1/chat", json={"question": "What are the salary bands?"}),
            await staff.post("/api/v1/chat", json={"question": PRIVATE_MARKER}),
        ]
    for resp in responses:
        assert PRIVATE_MARKER not in resp.text, resp.request.url
        assert "Salary bands" not in resp.text, resp.request.url
