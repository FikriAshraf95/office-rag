"""SPEC-04 §8 acceptance checks 1-9. Documents are ingested through the real worker with chosen chunks."""

from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.providers.base import RerankHit
from app.providers.errors import ProviderError
from app.providers.registry import Providers
from app.retrieval.search import Hit, cap_per_document, code_tokens, fetch_candidates, passes_gate, search
from app.security.identity import Identity
from tests.corpus import Corpus
from tests.helpers import PRIVATE_MARKER

BEN = Identity("ben", "Ben (Staff)", ("all",), True)
AISYAH = Identity("aisyah", "Aisyah (HR)", ("all", "hr"), True)


def cfg(**changes: Any) -> Settings:
    """Settings for one call; a gate threshold of 0 lets the vector arm pass unless a test sets it."""
    return get_settings().model_copy(update={"min_vector_sim": 0.0, **changes})


def ids(hits: list[Hit]) -> set[str]:
    return {str(h.document_id) for h in hits}


async def test_spec04_ac01_code_token_found_by_full_text_when_vector_ranks_low(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    await corpus.add(
        "Leave guide",
        [
            "annual leave 6 years service entitlement",
            "annual leave 6 years service balance",
            "annual leave 6 years service carry forward",
        ],
    )
    m2 = await corpus.add("Leave table", ["Grade M2 entitlement is 22 days"])
    settings = cfg(k_vec=2, min_vector_sim=0.99)
    hits = await search(db, "M2 annual leave 6 years", BEN, 20, settings=settings, providers=providers)
    found = [h for h in hits if str(h.document_id) == m2]
    assert found, "the M2 chunk must be returned"
    assert found[0].fts_rank is not None
    assert found[0].vec_rank is None


async def test_spec04_ac02_superseded_documents_are_never_retrieved(
    db: AsyncSession, client: httpx.AsyncClient, providers: Providers, corpus: Corpus
) -> None:
    body = ["maximum consecutive leave days is 5", "annual leave application form HR-F07"]
    old = await corpus.add("Handbook 2024", body)
    new = await corpus.add("Handbook 2026", body)
    assert (await client.patch(f"/api/v1/documents/{old}", json={"status": "superseded"})).status_code == 200
    for query in ["maximum consecutive leave days", "annual leave application", "HR-F07 form", "handbook"]:
        hits = await search(db, query, BEN, settings=cfg(), providers=providers)
        assert hits
        assert old not in ids(hits), query
        assert new in ids(hits), query


async def test_spec04_ac03_access_filter_runs_before_ranking(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    marker_text = f"{PRIVATE_MARKER} salary bands for grade M2 and M3 are confidential"
    private = await corpus.add("Salary bands", [marker_text], groups=["hr"])
    for i in range(3):
        await corpus.add(
            f"Public {i}", [f"salary bands grade overview number {i} part {j}" for j in range(4)]
        )
    settings = cfg()
    as_ben = await search(db, marker_text, BEN, settings=settings, providers=providers)
    assert private not in ids(as_ben)
    assert len(as_ben) == settings.top_k
    assert all(PRIVATE_MARKER not in h.text for h in as_ben)
    as_aisyah = await search(db, marker_text, AISYAH, settings=settings, providers=providers)
    assert private in ids(as_aisyah)


async def test_spec04_ac04_other_embedding_model_is_never_returned(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    await corpus.add("Guide", ["remote work equipment allowance", "remote work approval"])
    before = await search(db, "remote work", BEN, settings=cfg(), providers=providers)
    assert before
    await db.execute(text("UPDATE chunks SET embedding_model = 'other-model'"))
    after = await search(db, "remote work", BEN, settings=cfg(), providers=providers)
    assert after == []


async def test_spec04_ac05_at_most_max_chunks_per_document(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    big = await corpus.add("Big", [f"travel claim receipts rule {i}" for i in range(8)])
    await corpus.add("Small", ["travel claim receipts summary"])
    hits = await search(db, "travel claim receipts", BEN, settings=cfg(), providers=providers)
    from_big = [h for h in hits if str(h.document_id) == big]
    assert len(from_big) == get_settings().max_chunks_per_doc
    assert len(hits) == get_settings().max_chunks_per_doc + 1


async def test_spec04_ac06_unrelated_query_returns_nothing(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    await corpus.add("Office", ["parking bays are numbered", "the cafeteria opens at eight"])
    await corpus.add("Travel", ["flights are booked through the portal"])
    hits = await search(db, "pet policy", BEN, settings=cfg(min_vector_sim=0.6), providers=providers)
    assert hits == []


async def test_spec04_ac07_reranker_orders_and_failure_falls_back(
    db: AsyncSession, providers: Providers, corpus: Corpus, monkeypatch: pytest.MonkeyPatch
) -> None:
    await corpus.add("A", ["alpha only here"])
    await corpus.add("B", ["alpha beta gamma together"])
    await corpus.add("C", ["alpha beta in the middle"])
    plain = await search(db, "alpha beta gamma", BEN, settings=cfg(), providers=providers)
    assert all(h.rerank_score is None for h in plain)

    settings = cfg(rerank_model="fake-rerank")
    reranking = Providers(settings, providers.recorder)
    hits = await search(db, "alpha beta gamma", BEN, settings=settings, providers=reranking)
    scores = [h.rerank_score for h in hits]
    assert all(s is not None for s in scores)
    assert scores == sorted(scores, reverse=True)  # type: ignore[type-var]
    assert hits[0].title == "B"

    class Broken:
        model = "broken"

        async def rerank(self, *_: Any, **__: Any) -> list[RerankHit]:
            raise ProviderError("provider_unavailable", retryable=False, http_status=503)

    failing = Providers(settings, providers.recorder)
    monkeypatch.setattr(failing, "reranker", lambda: Broken())
    fallback = await search(db, "alpha beta gamma", BEN, settings=settings, providers=failing)
    assert [h.chunk_id for h in fallback] == [h.chunk_id for h in plain]
    assert all(h.rerank_score is None for h in fallback)


async def test_spec04_s4_reranker_score_is_the_gate_and_usage_is_logged(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    await corpus.add("A", ["alpha beta gamma together"])
    await corpus.add("B", ["completely unrelated words here"])
    # The vector gate is wide open; only the reranker score decides.
    settings = cfg(rerank_model="fake-rerank", min_rerank_score=0.5)
    reranking = Providers(settings, providers.recorder)
    hits = await search(db, "alpha beta gamma", BEN, settings=settings, providers=reranking)
    assert [h.title for h in hits] == ["A"]
    assert hits[0].rerank_score == 1.0
    none = cfg(rerank_model="fake-rerank", min_rerank_score=1.1)
    assert (
        await search(
            db, "alpha beta gamma", BEN, settings=none, providers=Providers(none, providers.recorder)
        )
        == []
    )


async def test_spec04_ac08_common_words_are_gated_out_but_code_tokens_pass(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    await corpus.add("Policies", ["the leave policy applies to everyone", "the travel policy is simple"])
    await corpus.add("Table", ["Grade M2 entitlement is 22 days"])
    strict = cfg(min_vector_sim=0.99)
    qvec = (await providers.embedder().embed(["pet policy"], purpose="question"))[0]
    candidates = await fetch_candidates(db, "pet policy", qvec, ["all"], strict)
    assert any(h.fts_rank is not None for h in candidates)
    assert await search(db, "pet policy", BEN, settings=strict, providers=providers) == []
    hits = await search(db, "M2 days", BEN, settings=strict, providers=providers)
    assert any("M2" in h.text for h in hits)


def test_spec04_ac08_code_token_rule() -> None:
    assert code_tokens("M2 annual leave 6 years") == ["M2"]
    assert code_tokens("form HR-F07 for Q4 2026") == ["HR-F07", "Q4"]
    assert code_tokens("pet policy 2026 10 days") == []


async def test_spec04_ac08_token_must_be_a_whole_word_in_a_full_text_hit(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    await corpus.add("Other", ["Grade M20 entitlement is 30 days"])
    strict = cfg(min_vector_sim=0.99)
    qvec = (await providers.embedder().embed(["M2"], purpose="question"))[0]
    candidates = await fetch_candidates(db, "M2", qvec, ["all"], strict)
    assert not passes_gate("M2", candidates, strict)


async def test_spec04_ac09_top_k_after_cap_across_documents(
    db: AsyncSession, providers: Providers, corpus: Corpus
) -> None:
    a = await corpus.add("A", [f"expense claim submission step {i}" for i in range(6)])
    await corpus.add("B", [f"expense claim approval step {i}" for i in range(3)])
    await corpus.add("C", [f"expense claim payment step {i}" for i in range(3)])
    settings = cfg()
    hits = await search(db, "expense claim step", BEN, settings=settings, providers=providers)
    assert len(hits) == settings.top_k
    assert sum(1 for h in hits if str(h.document_id) == a) <= settings.max_chunks_per_doc


def test_spec04_cap_keeps_order_and_drops_extras() -> None:
    def hit(doc: str, n: int) -> Hit:
        return Hit(
            n,
            doc,
            n,
            "text",
            "t",
            [],
            None,
            None,
            None,
            None,
            "T",
            "f",
            "pdf",
            None,
            None,
            None,
            0.1,
            n,
            None,
            None,
        )

    hits = [hit("a", 1), hit("a", 2), hit("b", 3), hit("a", 4)]
    assert [h.chunk_id for h in cap_per_document(hits, 2)] == [1, 2, 3]
