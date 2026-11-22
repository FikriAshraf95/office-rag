"""Throttling and retries (SPEC-06 §4). Each attempt is one provider call with its own usage row."""

import asyncio
import random
import time
from collections.abc import Awaitable, Callable

from app.providers.errors import ProviderError

Sleep = Callable[[float], Awaitable[None]]

MAX_BACKOFF_S = 30.0
DEFAULT_MAX_ATTEMPTS = 5


def backoff_delay(attempt: int, retry_after: float | None) -> float:
    """`Retry-After` when present; else min(30 s, 1 s * 2^attempt) + jitter(0-1 s)."""
    if retry_after is not None:
        return retry_after
    return min(MAX_BACKOFF_S, 2.0**attempt) + random.random()


async def with_retries[T](
    attempt: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Sleep = asyncio.sleep,
) -> T:
    for n in range(max_attempts):
        try:
            return await attempt()
        except ProviderError as exc:
            if not exc.retryable or n == max_attempts - 1:
                raise
            await sleep(backoff_delay(n, exc.retry_after))
    raise AssertionError("unreachable")


class Throttle:
    """Token bucket per model at `AI_MAX_RPM` requests per minute."""

    def __init__(self, rpm: int, sleep: Sleep = asyncio.sleep) -> None:
        self._rate = rpm / 60.0
        self._capacity = float(rpm)
        self._sleep = sleep
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, model: str) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                tokens, last = self._buckets.get(model, (self._capacity, now))
                tokens = min(self._capacity, tokens + (now - last) * self._rate)
                if tokens >= 1.0:
                    self._buckets[model] = (tokens - 1.0, now)
                    return
                self._buckets[model] = (tokens, now)
                wait = (1.0 - tokens) / self._rate
            await self._sleep(wait)
