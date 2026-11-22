"""Invariant (SPEC-00 §6.5, SPEC-05 §4): no answer with `found = true` reaches the user without a citation."""

import json
from typing import Any

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.answering.citations import MARKER
from app.config import get_settings
from app.db.models import Question
from app.providers.fakes import FakeChatModel
from app.providers.registry import Providers
from tests.corpus import Corpus

REPLIES = [
    "Fourteen days a year for confirmed staff [1].",
    "Fourteen days a year for confirmed staff.",
    "Fourteen days a year [7].",
    "Fourteen days [1, 7]. Managers get more [8].",
    "",
    "NOT_FOUND",
    "Fourteen days a year for confirmed staff [1]. Probation staff get none.",
]


def _final(body: str) -> dict[str, Any]:
    deltas: list[str] = []
    done: dict[str, Any] = {}
    for block in body.strip().split("\n\n"):
        name, data = (line.split(": ", 1)[1] for line in block.split("\n"))
        payload = json.loads(data)
        if name == "delta":
            deltas.append(payload["text"])
        if name == "done":
            done = payload
    return {"found": done["found"], "text": done.get("finalText", "".join(deltas))}


async def test_no_uncited_answer_is_shown_or_stored(
    client: httpx.AsyncClient,
    providers: Providers,
    corpus: Corpus,
    db: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)
    await corpus.add("Leave policy", ["Annual leave is fourteen days per year for confirmed staff."])
    fake = providers.chat("answer")
    assert isinstance(fake, FakeChatModel)
    fake.script(REPLIES)

    for _ in REPLIES:
        resp = await client.post("/api/v1/chat", json={"question": "How many days of annual leave?"})
        final = _final(resp.text)
        if final["found"]:
            assert MARKER.search(final["text"]), final
            assert "[7]" not in final["text"] and "[8]" not in final["text"]

    rows = (await db.execute(select(Question))).scalars().all()
    assert len(rows) == len(REPLIES)
    for row in rows:
        await db.refresh(row)
        assert row.found is not None
        if row.found:
            assert row.cited and row.answer and MARKER.search(row.answer)
        else:
            assert row.cited == []
