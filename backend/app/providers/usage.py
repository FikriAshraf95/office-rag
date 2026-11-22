"""Writes one `usage` row per provider call (SPEC-06 §6), keeps the latest balance headers, and reads the
usage summary for `GET /api/v1/usage/summary` (SPEC-08 §7; the API's only import from providers)."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import structlog
from sqlalchemy import ColumnElement, String, and_, cast, func, literal, select, true
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import InstrumentedAttribute

from app.db.models import Chunk, Document, Question, Usage
from app.providers.base import Purpose, TokenUsage, UsageRole
from app.providers.pricing import cost_myr

log = structlog.get_logger()

BALANCE_HEADERS = {
    "x-ilmu-token-balance": "token_balance",
    "x-ilmu-payg-balance-myr": "payg_balance_myr",
}


@dataclass(slots=True)
class UsageEntry:
    provider: str
    model: str
    role: UsageRole
    purpose: Purpose
    ref_id: str | None
    usage: TokenUsage
    latency_ms: int
    status: str
    error_code: str | None = None


class UsageRecorder:
    """Each write runs in its own short transaction, so a failed request still logs usage.

    Tests bind it to the test connection (savepoint) so the rows roll back with the test.
    """

    def __init__(self, bind: AsyncEngine | AsyncConnection, payg_alert_myr: float = 0.0) -> None:
        self.payg_alert_myr = Decimal(str(payg_alert_myr))
        if isinstance(bind, AsyncConnection):
            self._sessions = async_sessionmaker(
                bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
            )
        else:  # an engine: each write is its own transaction (join_transaction_mode is for connections)
            self._sessions = async_sessionmaker(bind, expire_on_commit=False)
        self.balances = LATEST_BALANCES.values

    async def record(self, entry: UsageEntry) -> None:
        tokens = entry.usage
        cost: Decimal | None = cost_myr(
            entry.provider, entry.model, tokens.prompt_tokens, tokens.completion_tokens
        )
        row = Usage(
            provider=entry.provider,
            model=entry.model,
            role=entry.role,
            purpose=entry.purpose,
            ref_id=entry.ref_id,
            prompt_tokens=tokens.prompt_tokens,
            completion_tokens=tokens.completion_tokens,
            reasoning_tokens=tokens.reasoning_tokens,
            total_tokens=tokens.total_tokens or tokens.prompt_tokens + tokens.completion_tokens,
            cost_myr=cost,
            latency_ms=entry.latency_ms,
            status=entry.status,
            error_code=entry.error_code,
        )
        try:
            session: AsyncSession
            async with self._sessions() as session:
                session.add(row)
                await session.commit()
        except Exception as exc:
            # Usage logging must never break the call it describes.
            log.error("usage_write_failed", error_type=type(exc).__name__)

    def note_balances(self, headers: Mapping[str, str]) -> None:
        for header, key in BALANCE_HEADERS.items():
            value = headers.get(header)
            if value is not None:
                LATEST_BALANCES.values[key] = value
                LATEST_BALANCES.read_at = datetime.now(UTC)
                log.info("provider_balance", **{key: value})
        payg = LATEST_BALANCES.payg_myr
        if "x-ilmu-payg-balance-myr" in headers and payg is not None and payg < self.payg_alert_myr:
            log.warning(
                "payg_balance_low", payg_balance_myr=str(payg), alert_below_myr=str(self.payg_alert_myr)
            )


@dataclass(slots=True)
class Balances:
    """The latest balance headers this process has seen (one per process; the API reads its own)."""

    values: dict[str, str] = field(default_factory=dict)
    read_at: datetime | None = None

    def _number(self, key: str) -> Decimal | None:
        try:
            return Decimal(self.values[key]) if key in self.values else None
        except InvalidOperation:
            return None

    @property
    def plan_tokens(self) -> int | None:
        value = self._number("token_balance")
        return int(value) if value is not None else None

    @property
    def payg_myr(self) -> Decimal | None:
        return self._number("payg_balance_myr")


LATEST_BALANCES = Balances()


# --- Summary (read only) ---


@dataclass(frozen=True, slots=True)
class ModelUsage:
    model: str
    role: str
    purpose: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    cost_myr: Decimal | None


@dataclass(frozen=True, slots=True)
class QuestionStats:
    count: int
    avg_latency_ms: float | None
    avg_first_token_ms: float | None
    avg_tokens: float | None


@dataclass(frozen=True, slots=True)
class IngestionStats:
    documents: int
    chunks: int
    embed_tokens: int


@dataclass(frozen=True, slots=True)
class UsageSummary:
    by_model: list[ModelUsage]
    questions: QuestionStats
    ingestion: IngestionStats
    balances: Balances


def _between(
    column: InstrumentedAttribute[datetime], start: datetime | None, end: datetime | None
) -> ColumnElement[bool]:
    clauses = [column >= start] if start is not None else []
    clauses += [column < end] if end is not None else []
    return and_(true(), *clauses)


async def summary(session: AsyncSession, start: datetime | None, end: datetime | None) -> UsageSummary:
    """Totals for `start <= at < end` (either may be None). Document and chunk counts are current state."""
    by_model = await session.execute(
        select(
            Usage.model,
            Usage.role,
            Usage.purpose,
            func.count(),
            func.coalesce(func.sum(Usage.prompt_tokens), 0),
            func.coalesce(func.sum(Usage.completion_tokens), 0),
            func.sum(Usage.cost_myr),
        )
        .where(_between(Usage.at, start, end))
        .group_by(Usage.model, Usage.role, Usage.purpose)
        .order_by(Usage.purpose, Usage.role, Usage.model)
    )
    per_question = (
        select(
            Question.latency_ms,
            Question.first_token_ms,
            func.coalesce(func.sum(Usage.total_tokens), 0).label("tokens"),
        )
        .outerjoin(
            Usage,
            and_(Usage.ref_id == cast(Question.id, String), Usage.purpose == literal("question")),
        )
        .where(_between(Question.created_at, start, end))
        .group_by(Question.id)
        .subquery()
    )
    q = (
        await session.execute(
            select(
                func.count(),
                func.avg(per_question.c.latency_ms),
                func.avg(per_question.c.first_token_ms),
                func.avg(per_question.c.tokens),
            )
        )
    ).one()
    documents = await session.scalar(select(func.count()).where(Document.deleted_at.is_(None)))
    chunks = await session.scalar(select(func.count()).select_from(Chunk))
    embed_tokens = (
        await session.execute(
            select(func.coalesce(func.sum(Usage.total_tokens), 0)).where(
                Usage.purpose == "ingestion", Usage.role == "embed", _between(Usage.at, start, end)
            )
        )
    ).scalar_one()

    def num(value: object) -> float | None:
        return float(value) if isinstance(value, (int, float, Decimal)) else None

    return UsageSummary(
        by_model=[ModelUsage(*row) for row in by_model.all()],
        questions=QuestionStats(int(q[0]), num(q[1]), num(q[2]), num(q[3])),
        ingestion=IngestionStats(documents or 0, chunks or 0, int(embed_tokens or 0)),
        balances=LATEST_BALANCES,
    )
