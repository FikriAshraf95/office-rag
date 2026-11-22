"""Documents whose chunk texts a test chooses, through the real API and worker (extraction is faked)."""

from collections.abc import Callable

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.ingestion import extract as extraction
from app.ingestion.chunking import WhitespaceCounter
from app.ingestion.types import ChunkDraft, DocMeta, IngestResult
from app.ingestion.worker import process_one_job
from app.providers.registry import Providers
from tests import uploads


class Corpus:
    def __init__(
        self,
        client: httpx.AsyncClient,
        client_as: Callable[[str | None], httpx.AsyncClient],
        sessions: async_sessionmaker[AsyncSession],
        providers: Providers,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self.client = client
        self.client_as = client_as
        self.sessions = sessions
        self.providers = providers
        self.monkeypatch = monkeypatch
        self.n = 0

    async def add(
        self, title: str, chunks: list[str], groups: list[str] | None = None, department: str | None = None
    ) -> str:
        drafts = [
            ChunkDraft("text", t, [title], len(t.split()), section=str(i)) for i, t in enumerate(chunks)
        ]
        self.monkeypatch.setattr(
            extraction, "extract", lambda *_, **__: IngestResult(list(drafts), DocMeta(language="en"))
        )
        self.n += 1
        fields: dict[str, str | list[str]] = {"title": title}
        if groups:
            fields["accessGroups"] = groups
        if department:
            fields["department"] = department
        owner = "aisyah" if groups else "ben"
        async with self.client_as(owner) as c:
            resp = await uploads.upload(c, uploads.pdf(f"c{self.n}-{title}"), f"{self.n}.pdf", **fields)
            assert resp.status_code == 202, resp.text
            doc_id = str(resp.json()["id"])
        await process_one_job(self.sessions, get_settings(), self.providers, WhitespaceCounter(), "w")
        return doc_id
