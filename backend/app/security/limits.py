"""Per-user limits for the public preview (SPEC-11 §5.2-5.3): chat limits protect the ILMU quota, and a
failed-login limit slows password guessing.

Chat limits apply only in `password` mode: a daily cap counted from `questions`, then an in-process token
bucket per user (one API process, so in-memory state is enough).
"""

import math
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.config import Settings
from app.db.models import Question
from app.security.identity import Identity

RATE_DETAIL = "You're asking questions faster than the preview allows. Wait a moment and try again."
DAILY_DETAIL = "You've reached today's question limit for the preview. Try again tomorrow (00:00 UTC)."


@dataclass(slots=True)
class _Bucket:
    tokens: float
    at: float


class ChatLimiter:
    """Token bucket per user: `per_min` questions at once, refilled at `per_min` per minute."""

    def __init__(self, per_min: int, clock: Callable[[], float] | None = None) -> None:
        self.capacity = float(per_min)
        self.rate = per_min / 60.0
        self._clock = clock or time.monotonic
        self._buckets: dict[str, _Bucket] = {}

    def take(self, user_id: str) -> float | None:
        """Takes one token. Returns None when allowed, else the seconds until one is free."""
        now = self._clock()
        bucket = self._buckets.get(user_id)
        if bucket is None:
            bucket = self._buckets[user_id] = _Bucket(self.capacity, now)
        bucket.tokens = min(self.capacity, bucket.tokens + (now - bucket.at) * self.rate)
        bucket.at = now
        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return None
        return (1.0 - bucket.tokens) / self.rate if self.rate > 0 else 60.0


def _too_many(detail: str, retry_after: float) -> ApiError:
    return ApiError(
        429, "user_rate_limited", detail, headers={"Retry-After": str(max(1, math.ceil(retry_after)))}
    )


async def enforce_chat_limits(
    session: AsyncSession, user: Identity, settings: Settings, limiter: ChatLimiter
) -> None:
    if settings.auth_mode != "password":
        return
    now = datetime.now(UTC)
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today = await session.scalar(
        select(func.count())
        .select_from(Question)
        .where(Question.user_id == user.id, Question.created_at >= midnight)
    )
    if (today or 0) >= settings.chat_daily_cap:
        seconds_left = 86400 - (now - midnight).total_seconds()
        raise _too_many(DAILY_DETAIL, seconds_left)
    wait = limiter.take(user.id)
    if wait is not None:
        raise _too_many(RATE_DETAIL, wait)


LOGIN_DETAIL = "Too many failed sign-ins for this username. Wait 15 minutes and try again."


class LoginLimiter:
    """At most `max_failures` failed logins per username in `window` seconds (in-process)."""

    def __init__(
        self, max_failures: int = 10, window: float = 900.0, clock: Callable[[], float] | None = None
    ) -> None:
        self.max_failures = max_failures
        self.window = window
        self._clock = clock or time.monotonic
        self._failures: dict[str, deque[float]] = {}

    def _recent(self, username: str) -> deque[float]:
        now = self._clock()
        failures = self._failures.setdefault(username, deque())
        while failures and now - failures[0] >= self.window:
            failures.popleft()
        return failures

    def check(self, username: str) -> None:
        failures = self._recent(username)
        if len(failures) >= self.max_failures:
            raise _too_many(LOGIN_DETAIL, self.window - (self._clock() - failures[0]))

    def failed(self, username: str) -> None:
        if len(self._failures) > 10_000:  # guessed usernames must not grow memory without bound
            self._failures.clear()
        self._recent(username).append(self._clock())

    def succeeded(self, username: str) -> None:
        self._failures.pop(username, None)
