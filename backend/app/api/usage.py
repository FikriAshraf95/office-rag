"""Endpoint 14: usage and cost totals, balances (SPEC-08 §7)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    BalancesOut,
    IngestionStatsOut,
    QuestionStatsOut,
    UsageByModelOut,
    UsageSummaryOut,
)
from app.db.engine import get_session
from app.providers.usage import summary
from app.security.identity import CurrentUser

router = APIRouter(prefix="/api/v1", tags=["usage"])

Session = Annotated[AsyncSession, Depends(get_session)]


@router.get("/usage/summary", response_model=UsageSummaryOut)
async def usage_summary(
    session: Session,
    user: CurrentUser,
    start: Annotated[datetime | None, Query(alias="from")] = None,
    end: Annotated[datetime | None, Query(alias="to")] = None,
) -> UsageSummaryOut:
    s = await summary(session, start, end)
    payg = s.balances.payg_myr
    return UsageSummaryOut(
        by_model=[
            UsageByModelOut(
                model=m.model,
                role=m.role,
                purpose=m.purpose,
                calls=m.calls,
                prompt_tokens=m.prompt_tokens,
                completion_tokens=m.completion_tokens,
                cost_myr=float(m.cost_myr) if m.cost_myr is not None else None,
            )
            for m in s.by_model
        ],
        questions=QuestionStatsOut(
            count=s.questions.count,
            avg_latency_ms=s.questions.avg_latency_ms,
            avg_first_token_ms=s.questions.avg_first_token_ms,
            avg_tokens=s.questions.avg_tokens,
        ),
        ingestion=IngestionStatsOut(
            documents=s.ingestion.documents, chunks=s.ingestion.chunks, embed_tokens=s.ingestion.embed_tokens
        ),
        balances=BalancesOut(
            plan_tokens=s.balances.plan_tokens,
            payg_myr=float(payg) if payg is not None else None,
            read_at=s.balances.read_at,
        ),
    )
