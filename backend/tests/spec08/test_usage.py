"""Endpoint 14: GET /api/v1/usage/summary (SPEC-08 §7)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest

from app.config import get_settings
from app.providers import usage
from app.providers.registry import Providers
from tests.corpus import Corpus


async def test_usage_summary_counts_questions_tokens_and_balances(
    client: httpx.AsyncClient, providers: Providers, corpus: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)
    monkeypatch.setattr(usage, "LATEST_BALANCES", usage.Balances())
    await corpus.add("Leave policy", ["Annual leave is fourteen days per year for confirmed staff."])
    resp = await client.post("/api/v1/chat", json={"question": "How many days of annual leave?"})
    assert resp.status_code == 200
    providers.recorder.note_balances({"x-ilmu-token-balance": "41000", "x-ilmu-payg-balance-myr": "12.50"})

    body: dict[str, Any] = (await client.get("/api/v1/usage/summary")).json()
    assert set(body) == {"byModel", "questions", "ingestion", "balances"}
    assert body["questions"]["count"] >= 1 and body["questions"]["avgTokens"] > 0
    assert body["questions"]["avgFirstTokenMs"] is not None
    question_roles = {(m["role"], m["purpose"]) for m in body["byModel"]}
    assert {("embed", "question"), ("answer", "question"), ("embed", "ingestion")} <= question_roles
    assert body["ingestion"]["documents"] >= 1 and body["ingestion"]["chunks"] >= 1
    assert body["ingestion"]["embedTokens"] > 0
    assert body["balances"]["planTokens"] == 41000 and body["balances"]["paygMyr"] == 12.5
    assert body["balances"]["readAt"] is not None

    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    later: dict[str, Any] = (await client.get("/api/v1/usage/summary", params={"from": future})).json()
    assert later["byModel"] == [] and later["questions"]["count"] == 0
