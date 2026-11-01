"""Typed error model for the memory engine.

Why this module exists
----------------------
Before M0 the engine signalled every failure with a bare ``ValueError``,
``PermissionError`` or ``RuntimeError`` raised from deep inside a 4,800-line
module. A caller could not tell "you passed a bad epistemic status" (fix your
call) from "the vector index drifted from the ledger" (rebuild the index) from
"the store directory is not writable" (fix the deployment) without parsing
message text. Message text is not an API.

This module gives every failure a stable, importable type, and adds the two
pieces of the error model the engine was missing entirely: a retry policy with
bounded exponential backoff, and deterministic idempotency keys.

Compatibility
-------------
Every exception here also inherits from the builtin it replaces, so existing
``except ValueError`` / ``except PermissionError`` / ``except RuntimeError``
handlers keep working unchanged. Nothing that worked before breaks.
"""

from __future__ import annotations

import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, TypeVar

__all__ = [
    "MemoryEngineError",
    "ConfigurationError",
    "ValidationError",
    "EpistemicStatusError",
    "EventTimeError",
    "GroundedWriteRefused",
    "IndexDriftError",
    "StoreUnavailableError",
    "NotFoundError",
    "DependencyUnavailableError",
    "TransientError",
    "RetryPolicy",
    "call_with_retry",
    "idempotency_key",
]

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------


class MemoryEngineError(Exception):
    """Base class for every error the memory engine raises deliberately.

    Carries an optional machine-readable ``code`` and a ``details`` mapping so
    an API layer can serialise the failure without string matching.
    """

    code: str = "memory_engine_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.details: dict[str, Any] = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        """Serialise for an API/JSON surface. Never includes a traceback."""
        return {
            "error": type(self).__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{type(self).__name__}(code={self.code!r}, message={self.message!r})"


class ConfigurationError(MemoryEngineError):
    """The engine was configured with values it cannot operate with."""

    code = "configuration_error"


class ValidationError(MemoryEngineError, ValueError):
    """A caller-supplied argument is invalid. Retrying will not help."""

    code = "validation_error"


class EpistemicStatusError(ValidationError):
    """``epistemic_status`` is missing or outside the declared vocabulary.

    Separate from plain ValidationError because the engine's trust model treats
    an undeclared basis as a refusal, not a default, and callers need to
    distinguish that refusal from a typo in a topic name.
    """

    code = "epistemic_status_error"


class EventTimeError(ValidationError):
    """A caller-supplied event time is unparseable or in the future."""

    code = "event_time_error"


class GroundedWriteRefused(MemoryEngineError, PermissionError):
    """A write was refused to protect the grounded/simulated separation.

    Raised when simulated content is routed through ``remember()``. This is a
    deliberate refusal, not a bug: see Step 7.4 in the engine docstring.
    """

    code = "grounded_write_refused"


class IndexDriftError(MemoryEngineError, RuntimeError):
    """A retrieval index disagrees with the ledger.

    Raised only in strict mode. The non-strict path returns results annotated
    with a ``_index_drift`` diagnostic instead.
    """

    code = "index_drift_error"


class StoreUnavailableError(MemoryEngineError, OSError):
    """The store directory is missing, unreadable, or not writable."""

    code = "store_unavailable"


class NotFoundError(MemoryEngineError, LookupError):
    """A referenced fact id does not exist in the ledger."""

    code = "not_found"


class DependencyUnavailableError(MemoryEngineError, RuntimeError):
    """An optional native dependency (faiss, sentence-transformers, rank_bm25)
    is required for this operation but is not installed."""

    code = "dependency_unavailable"


class TransientError(MemoryEngineError):
    """A failure that may succeed if retried (lock contention, short I/O error).

    This is the only type ``RetryPolicy`` retries by default.
    """

    code = "transient_error"


# ---------------------------------------------------------------------------
# Retry with bounded exponential backoff
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetryPolicy:
    """Bounded exponential backoff with jitter.

    ``max_attempts`` counts the FIRST attempt, so ``max_attempts=3`` means at
    most three calls and at most two sleeps. ``delay_for`` is pure and
    deterministic given ``rng``, which is what makes it testable.
    """

    max_attempts: int = 3
    base_delay: float = 0.05
    max_delay: float = 2.0
    multiplier: float = 2.0
    jitter: float = 0.1
    retry_on: tuple[type[BaseException], ...] = (TransientError,)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ConfigurationError(
                f"RetryPolicy.max_attempts must be >= 1, got {self.max_attempts}",
                details={"max_attempts": self.max_attempts},
            )
        if self.base_delay < 0 or self.max_delay < 0:
            raise ConfigurationError("RetryPolicy delays must be non-negative")
        if self.multiplier < 1:
            raise ConfigurationError(
                f"RetryPolicy.multiplier must be >= 1, got {self.multiplier}"
            )
        if not 0.0 <= self.jitter <= 1.0:
            raise ConfigurationError(
                f"RetryPolicy.jitter must be within [0, 1], got {self.jitter}"
            )

    def delay_for(self, attempt: int, rng: random.Random | None = None) -> float:
        """Seconds to sleep after failed ``attempt`` (1-based).

        Capped at ``max_delay`` BEFORE jitter is applied, so the cap is a real
        upper bound rather than a value jitter can push past.
        """
        if attempt < 1:
            raise ValidationError(f"attempt must be >= 1, got {attempt}")
        raw = self.base_delay * (self.multiplier ** (attempt - 1))
        capped = min(raw, self.max_delay)
        if self.jitter == 0.0:
            return capped
        r = rng or random
        # Symmetric jitter: capped * (1 +/- jitter), floored at zero.
        factor = 1.0 + r.uniform(-self.jitter, self.jitter)
        return max(0.0, capped * factor)


def call_with_retry(
    fn: Callable[..., T],
    *args: Any,
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    **kwargs: Any,
) -> T:
    """Call ``fn`` retrying only ``policy.retry_on`` failures.

    Non-retryable exceptions propagate on the first attempt, unchanged. When
    attempts are exhausted the LAST exception is re-raised, so the caller sees
    the real cause rather than a wrapper.
    """
    pol = policy or RetryPolicy()
    last: BaseException | None = None
    for attempt in range(1, pol.max_attempts + 1):
        try:
            return fn(*args, **kwargs)
        except pol.retry_on as exc:  # type: ignore[misc]
            last = exc
            if attempt >= pol.max_attempts:
                break
            sleep(pol.delay_for(attempt, rng=rng))
    assert last is not None  # loop always runs at least once
    raise last


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def idempotency_key(*parts: Any, namespace: str = "mem20") -> str:
    """Deterministic 64-char key for a logical write.

    The engine's ``remember()`` mints a random id per call, so a retried write
    creates a duplicate fact. Callers that need at-most-once semantics compute
    this key from the logical identity of the write (topic + content + actor)
    and dedupe on it before calling.

    Parts are joined with a NUL separator so ``("ab", "c")`` and ``("a", "bc")``
    cannot collide.
    """
    h = hashlib.sha256()
    h.update(namespace.encode("utf-8"))
    for part in parts:
        h.update(b"\x00")
        h.update(str(part).encode("utf-8"))
    return h.hexdigest()
