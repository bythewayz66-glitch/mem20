"""memory_engine — the mem20 tiered memory subsystem.

This package is the supported public surface. Before M0 ``__init__.py`` was
0 bytes, so the only way to use the engine was ``from memory_engine import
memory`` and then reach into a 4,800-line module of undocumented free
functions. Nothing was declared, so nothing could be depended on.

What is stable
--------------
Everything named in ``__all__`` below. That is the contract:

* ``MemoryEngine`` — typed facade (``memory_engine.api``)
* the error model (``memory_engine.errors``)
* ``EngineConfig`` (``memory_engine.config``)
* the engine's free functions, re-exported lazily so ``import memory_engine``
  stays cheap and does not pull in numpy/faiss/sentence-transformers

Anything else reachable through ``memory_engine.memory.<name>`` is internal and
may change without notice.

Import cost
-----------
``import memory_engine`` imports only this file. The engine module (and its
optional native dependencies) is imported on first attribute access. That
matters because ``sentence_transformers`` alone costs seconds to import, and a
CLI that only wants ``EngineConfig`` should not pay for it.

Store path
----------
The engine resolves its store at import time from ``MEM20_STORE_PATH``
(default ``~/.mem20/store``). Set the environment before the first access:

    import os
    os.environ["MEM20_STORE_PATH"] = "/var/lib/mem20/store"
    from memory_engine import MemoryEngine
"""

from __future__ import annotations

from typing import Any

from .api import EPISTEMIC_STATUSES, UNLABELED, Fact, HealthReport, MemoryEngine
from .config import DEFAULT_STORE_PATH, EngineConfig
from .errors import (
    ConfigurationError,
    DependencyUnavailableError,
    EpistemicStatusError,
    EventTimeError,
    GroundedWriteRefused,
    IndexDriftError,
    MemoryEngineError,
    NotFoundError,
    RetryPolicy,
    StoreUnavailableError,
    TransientError,
    ValidationError,
    call_with_retry,
    idempotency_key,
)

__version__ = "3.1.2"

#: Names re-exported from ``memory_engine.memory``. Resolved lazily by
#: ``__getattr__`` so importing the package does not import the engine.
_ENGINE_EXPORTS = frozenset(
    {
        "remember",
        "remember_simulated",
        "recall",
        "recall_at",
        "recall_semantic",
        "recall_hybrid",
        "recall_graph",
        "supersede",
        "rebuild_index",
        "rebuild_vectors",
        "rebuild_bm25",
        "rebuild_graph",
        "index_health",
        "status",
        "ledger_view",
        "backup",
        "detect_secrets",
        "redact_secrets",
        "detect_knowledge_gaps",
        "self_audit",
        "label_coverage",
        "audit_contamination",
        "promote_simulated_to_grounded",
        "quarantine_expired_simulated",
        "list_simulated",
        "validate_epistemic_status",
        "validate_event_time",
        "main",
    }
)

__all__ = [
    # facade
    "MemoryEngine",
    "Fact",
    "HealthReport",
    # config
    "EngineConfig",
    "DEFAULT_STORE_PATH",
    # error model
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
    # vocabulary
    "EPISTEMIC_STATUSES",
    "UNLABELED",
    # engine functions (lazy)
    *sorted(_ENGINE_EXPORTS),
    "__version__",
]


def __getattr__(name: str) -> Any:
    """Resolve engine functions on first access (PEP 562)."""
    if name in _ENGINE_EXPORTS:
        from . import memory as _engine

        try:
            return getattr(_engine, name)
        except AttributeError as exc:  # pragma: no cover - contract drift guard
            raise AttributeError(
                f"memory_engine declares {name!r} in its public surface but "
                f"memory_engine.memory does not define it. The contract and the "
                f"engine have drifted."
            ) from exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
