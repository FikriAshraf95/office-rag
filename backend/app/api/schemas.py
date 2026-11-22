"""Response and request schemas. JSON is camelCase (SPEC-00 §6.2)."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class HealthOut(CamelModel):
    status: Literal["ok", "error"]
    db: Literal["ok", "error"]
    ai_provider: str


class DemoUserOut(CamelModel):
    id: str
    name: str
    groups: list[str]


class ConfigOut(CamelModel):
    allowed_extensions: list[str]
    max_upload_bytes: int
    demo_users: list[DemoUserOut]
    access_groups: list[str]
    doc_types: list[str]
    org_name: str


class MeOut(CamelModel):
    id: str
    name: str
    groups: list[str]


class ProblemOut(CamelModel):
    """application/problem+json (SPEC-08 §2). Extra members are allowed per code."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")

    status: int
    code: str
    title: str
    detail: str
    trace_id: str
    errors: dict[str, list[str]] | None = None


class DocumentOut(CamelModel):
    """SPEC-08 §4 Document."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    title: str
    filename: str
    file_type: str
    content_type: str
    size_bytes: int
    doc_type: str
    department: str | None
    effective_date: date | None
    version: str | None
    language: str | None
    status: Literal["current", "superseded"]
    access_groups: list[str]
    page_count: int | None
    summary: str | None
    tags: list[str]
    ingest_status: Literal["queued", "processing", "ready", "failed"]
    ingest_error_code: str | None
    ingest_error: str | None
    chunk_count: int
    uploaded_by: str
    created_at: datetime
    updated_at: datetime


class DocumentListOut(CamelModel):
    items: list[DocumentOut]


class DocumentPatch(CamelModel):
    """PATCH body: send only what changes. `null` clears department, effectiveDate and version."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    title: str | None = None
    doc_type: str | None = None
    department: str | None = None
    effective_date: date | None = None
    version: str | None = None
    status: Literal["current", "superseded"] | None = None
    access_groups: list[str] | None = None


class ChunkOut(CamelModel):
    """SPEC-08 §4.7 chunk. No embedding, no access groups: callers get text and where it came from."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    ordinal: int
    chunk_type: str
    text: str
    heading_path: list[str]
    section: str | None
    page_start: int | None
    page_end: int | None
    sheet: str | None
    token_count: int


class ChunkListOut(CamelModel):
    items: list[ChunkOut]
    total: int


class SearchIn(CamelModel):
    query: str
    top_k: int | None = Field(default=None, ge=1, le=20)


class SearchHitOut(CamelModel):
    """SPEC-08 §5 hit: where it came from, why it ranked, and a 300-char snippet."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    file_type: str
    heading_path: list[str]
    section: str | None
    page_start: int | None
    page_end: int | None
    sheet: str | None
    effective_date: date | None
    score: float
    vec_rank: int | None
    fts_rank: int | None
    vec_sim: float | None
    rerank_score: float | None
    snippet: str


class SearchOut(CamelModel):
    hits: list[SearchHitOut]


class ChatTurnIn(CamelModel):
    """One earlier turn: model context only, never a source (SPEC-05 §1)."""

    question: str = Field(max_length=1000)
    answer: str = Field(max_length=4000)


class ChatIn(CamelModel):
    question: str
    history: list[ChatTurnIn] = Field(default_factory=list, max_length=4)


# SSE event payloads (SPEC-05 §6). FastAPI can't describe them; app.export_openapi adds them (SPEC-08 §6).


class SseMeta(CamelModel):
    question_id: uuid.UUID


class SseSource(CamelModel):
    n: int
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    title: str
    file_type: str
    heading_path: list[str]
    section: str | None
    page_start: int | None
    page_end: int | None
    sheet: str | None
    effective_date: date | None
    snippet: str


class SseSources(CamelModel):
    sources: list[SseSource]


class SseDelta(CamelModel):
    text: str


class SseUsage(CamelModel):
    prompt_tokens: int
    completion_tokens: int


class SseDone(CamelModel):
    found: bool
    cited: list[int]
    final_text: str | None = Field(
        default=None, description="Present only when it replaces the streamed text"
    )
    model: str | None = Field(description="The model actually used; null when no model was called")
    usage: SseUsage
    latency_ms: int
    first_token_ms: int | None


class SseError(CamelModel):
    code: str
    detail: str


SSE_EVENTS: dict[str, type[CamelModel]] = {
    "meta": SseMeta,
    "sources": SseSources,
    "delta": SseDelta,
    "done": SseDone,
    "error": SseError,
}


class UsageByModelOut(CamelModel):
    model: str
    role: str
    purpose: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    cost_myr: float | None


class QuestionStatsOut(CamelModel):
    count: int
    avg_latency_ms: float | None
    avg_first_token_ms: float | None
    avg_tokens: float | None


class IngestionStatsOut(CamelModel):
    documents: int
    chunks: int
    embed_tokens: int


class BalancesOut(CamelModel):
    """Latest `x-ilmu-token-balance` / `x-ilmu-payg-balance-myr` this API process has seen."""

    plan_tokens: int | None
    payg_myr: float | None
    read_at: datetime | None


class UsageSummaryOut(CamelModel):
    by_model: list[UsageByModelOut]
    questions: QuestionStatsOut
    ingestion: IngestionStatsOut
    balances: BalancesOut
