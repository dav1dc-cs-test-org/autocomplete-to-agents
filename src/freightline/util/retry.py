"""Retry with exponential backoff, used by the carrier adapters."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay_seconds: float = 0.2
    max_delay_seconds: float = 2.0
    jitter: bool = True

    def delay_for(self, attempt: int) -> float:
        """Delay before ``attempt`` (1-based). Capped, optionally jittered."""
        raw = self.base_delay_seconds * (2 ** max(attempt - 1, 0))
        capped = min(raw, self.max_delay_seconds)
        if not self.jitter:
            return capped
        return capped * random.uniform(0.5, 1.0)  # noqa: S311 - backoff jitter, not crypto


def with_retries(
    operation: Callable[[], T],
    *,
    policy: RetryPolicy | None = None,
    retry_on: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError),
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``operation`` until it succeeds or the policy is exhausted."""
    active = policy or RetryPolicy()
    last_error: BaseException | None = None
    for attempt in range(1, active.attempts + 1):
        try:
            return operation()
        except retry_on as exc:
            last_error = exc
            if attempt == active.attempts:
                break
            sleep(active.delay_for(attempt))
    assert last_error is not None  # noqa: S101 - unreachable unless attempts < 1
    raise last_error
