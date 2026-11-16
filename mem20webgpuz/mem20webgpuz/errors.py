"""mem20webgpuz error model.

A single exception root so callers can catch one type, plus a small set of
typed subclasses that carry machine-readable ``details``. The retry policy and
the idempotency-key helper live here too, because they are part of the error
contract rather than the domain: a caller that wants to retry a failed job
needs both the exception taxonomy and the backoff rule in one place.

Nothing in this module imports a sibling subsystem, so it is safe to import
from anywhere (including the CLI's ``--help`` path, which must stay cheap).
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, TypeVar

__all__ = [
    "WebGPUError",
    "ConfigurationError",
    "ValidationError",
    "BackendUnavailableError",
    "QuotaExceededError",
    "JobCancelledError",
    "JobNotFoundError",
    "TransientError",
    "RetryPolicy",
    "call_with_retry",
    "idempotency_key",
]

T = TypeVar("T")


class WebGPUError(Exception):
    """Root of the mem20webgpuz error taxonomy."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": type(self).__name__,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(WebGPUError):
    """Environment or config value is unusable."""


class ValidationError(WebGPUError):
    """A request or roadmap failed validation at a boundary."""


class BackendUnavailableError(WebGPUError):
    """The requested execution backend cannot be reached or does not exist."""


class QuotaExceededError(WebGPUError):
    """A bounded resource (queue depth, payload size, workgroups) was exceeded."""


class JobCancelledError(WebGPUError):
    """The job was cancelled before it produced a result."""


class JobNotFoundError(WebGPUError):
    """No job with the given id exists in the store."""


class TransientError(WebGPUError):
    """A failure that is worth retrying (peer blip, lock contention)."""


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff with jitter.

    ``max_attempts`` counts the *total* attempts, so ``max_attempts=1`` means
    "do not retry". ``base_delay`` is the first sleep; each subsequent sleep is
    ``base_delay * factor ** (attempt - 1)`` capped at ``max_delay``, then
    multiplied by a jitter factor in ``[1 - jitter, 1]`` so a fleet of callers
    does not retry in lockstep.
    """

    max_attempts: int = 3
    base_delay: float = 0.05
    factor: float = 2.0
    max_delay: float = 2.0
    jitter: float = 0.25

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ConfigurationError(
                "max_attempts must be >= 1", details={"max_attempts": self.max_attempts}
            )
        if self.base_delay < 0 or self.max_delay < 0:
            raise ConfigurationError("delays must be non-negative")
        if not 0.0 <= self.jitter <= 1.0:
            raise ConfigurationError(
                "jitter must be within [0, 1]", details={"jitter": self.jitter}
            )

    def delay_for(self, attempt: int, *, rng: random.Random | None = None) -> float:
        """Seconds to sleep before ``attempt`` (1-based)."""
        if attempt < 1:
            raise ValidationError("attempt is 1-based", details={"attempt": attempt})
        raw = min(self.max_delay, self.base_delay * (self.factor ** (attempt - 1)))
        r = rng or random
        return max(0.0, raw * (1.0 - self.jitter * r.random()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "base_delay": self.base_delay,
            "factor": self.factor,
            "max_delay": self.max_delay,
            "jitter": self.jitter,
        }


def call_with_retry(
    fn: Callable[[], T],
    *,
    policy: RetryPolicy | None = None,
    retry_on: tuple[type[BaseException], ...] = (TransientError,),
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Call ``fn`` with bounded retries.

    Only exceptions in ``retry_on`` are retried; anything else propagates on the
    first raise. The final failure re-raises the last exception unchanged so the
    caller keeps the original type and details.
    """
    pol = policy or RetryPolicy()
    last: BaseException | None = None
    for attempt in range(1, pol.max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:  # type: ignore[misc]
            last = exc
            if attempt >= pol.max_attempts:
                break
            if on_retry is not None:
                on_retry(attempt, exc)
            sleep(pol.delay_for(attempt + 1))
    assert last is not None
    raise last


def idempotency_key(*parts: Any, namespace: str = "mem20webgpuz") -> str:
    """Deterministic key for a request, so a replay returns the first result.

    Canonical JSON (sorted keys, no whitespace) is hashed so two callers that
    build the same request in a different key order get the same key.
    """
    payload = json.dumps(
        {"namespace": namespace, "parts": list(parts)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
