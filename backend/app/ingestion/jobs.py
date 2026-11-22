"""The job queue (SPEC-03 §3): enqueue, claim with SKIP LOCKED, heartbeat, stale recovery.

Jobs are never written outside this module and `service.py`. Functions here do not commit unless said so;
the caller owns the transaction.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Job

INGEST_DOCUMENT = "ingest_document"
STALE_AFTER_MINUTES = 15
BACKOFF_BASE_S = 30

CLAIM_SQL = text(
    """
    UPDATE jobs SET status = 'running', locked_by = :worker, locked_at = now(), attempts = attempts + 1
    WHERE id = (
        SELECT id FROM jobs WHERE status = 'queued' AND run_after <= now()
        ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1
    )
    RETURNING id, kind, document_id, attempts, max_attempts
    """
)


@dataclass(frozen=True, slots=True)
class ClaimedJob:
    id: int
    kind: str
    document_id: uuid.UUID | None
    attempts: int
    max_attempts: int

    @property
    def can_retry(self) -> bool:
        return self.attempts < self.max_attempts

    @property
    def backoff_seconds(self) -> int:
        """SPEC-03 §3: 30 s * 2^attempts."""
        return int(BACKOFF_BASE_S * 2**self.attempts)


async def enqueue(session: AsyncSession, kind: str, document_id: uuid.UUID) -> Job:
    """Add a queued job in the caller's transaction; the caller commits."""
    job = Job(kind=kind, document_id=document_id)
    session.add(job)
    await session.flush()
    return job


async def claim(session: AsyncSession, worker_id: str) -> ClaimedJob | None:
    """Take the oldest runnable job and commit, so the claim is visible. Two workers never get one job."""
    row = (await session.execute(CLAIM_SQL, {"worker": worker_id})).one_or_none()
    await session.commit()
    if row is None:
        return None
    return ClaimedJob(
        id=row.id,
        kind=row.kind,
        document_id=row.document_id,
        attempts=row.attempts,
        max_attempts=row.max_attempts,
    )


async def heartbeat(session: AsyncSession, job_id: int, worker_id: str) -> None:
    """Keep a slow job from looking dead. Commits."""
    await session.execute(
        update(Job)
        .where(Job.id == job_id, Job.status == "running", Job.locked_by == worker_id)
        .values(locked_at=text("now()"))
    )
    await session.commit()


async def requeue_stale(session: AsyncSession, minutes: int = STALE_AFTER_MINUTES) -> int:
    """Running jobs with no heartbeat for `minutes` go back to the queue. Commits; returns the count."""
    result = await session.execute(
        update(Job)
        .where(Job.status == "running", Job.locked_at < func.now() - timedelta(minutes=minutes))
        .values(status="queued", locked_by=None, locked_at=None)
        .returning(Job.id)
    )
    count = len(result.all())
    await session.commit()
    return count


async def mark_done(session: AsyncSession, job_id: int) -> None:
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status="done",
            error_code=None,
            error=None,
            locked_by=None,
            locked_at=None,
            finished_at=text("now()"),
        )
    )


async def mark_failed(session: AsyncSession, job_id: int, code: str, message: str) -> None:
    await session.execute(
        update(Job)
        .where(Job.id == job_id)
        .values(
            status="failed",
            error_code=code,
            error=message,
            locked_by=None,
            locked_at=None,
            finished_at=text("now()"),
        )
    )


async def mark_retry(session: AsyncSession, job: ClaimedJob, code: str, message: str) -> None:
    """Back to the queue with the SPEC-03 §3 backoff."""
    await session.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(
            status="queued",
            error_code=code,
            error=message,
            locked_by=None,
            locked_at=None,
            run_after=datetime.now(UTC) + timedelta(seconds=job.backoff_seconds),
        )
    )
