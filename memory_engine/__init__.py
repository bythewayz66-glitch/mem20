"""memory_engine — the mem20 tiered memory subsystem.

Public surface: everything in ``__all__``. Lazy exports keep import cheap.
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

__version__ = "4.0.0"

_ENGINE_EXPORTS = frozenset(
    {
        "remember", "remember_simulated", "recall", "recall_at", "recall_semantic",
        "recall_hybrid", "recall_graph", "supersede", "rebuild_index", "rebuild_vectors",
        "rebuild_bm25", "rebuild_graph", "index_health", "status", "ledger_view", "backup",
        "detect_secrets", "redact_secrets", "detect_knowledge_gaps", "self_audit",
        "label_coverage", "audit_contamination", "promote_simulated_to_grounded",
        "quarantine_expired_simulated", "list_simulated", "validate_epistemic_status",
        "validate_event_time", "main",
        "procedural_add_skill", "procedural_get_skill", "procedural_find_skills",
        "procedural_execute_skill", "procedural_learn", "procedural_list_skills",
    }
)

_PREDICTIVE_EXPORTS = frozenset({
    "predict_next", "prefetch", "record_recall_outcome", "predictive_health",
    "get_predictive", "PredictiveRecall", "Prediction", "PrefetchResult",
})
_TEMPORAL_EXPORTS = frozenset({
    "as_of", "timeline", "diff", "snapshot", "temporal_health", "TimelineEvent", "DiffResult",
})
_EPISODIC_EXPORTS = frozenset({
    "create_episode", "add_event", "link_episodes", "recall_episodes", "episode_graph",
    "forget_episode", "list_episodes", "episodic_health", "Episode",
})
_INGEST_EXPORTS = frozenset({"ingest", "ingest_batch", "ingest_health"})
_SKILLS_EXPORTS = frozenset({
    "export_skill", "import_skill", "transfer_skill", "list_transferred_skills", "skills_health",
})
_SEARCH_EXPORTS = frozenset({"cognitive_search", "search_health"})
_SESSION_EXPORTS = frozenset({"save_session", "load_session", "list_sessions", "session_health"})
_VERIFY_EXPORTS = frozenset({"verify_claim", "verify_prediction", "verify_batch", "verify_health"})

_FORGETTING_EXPORTS = frozenset({
    "retention", "reinforce", "review_state", "track", "item_state",
    "review", "review_queue", "forgetting_health",
})
_WORKING_EXPORTS = frozenset({
    "working_put", "working_get", "list_working", "working_clear", "working_flush", "flush", "working_health",
})
_CONSOLIDATE_EXPORTS = frozenset({
    "prune_superseded", "consolidate_topic", "promote_all_due_simulated", "consolidate_health",
})
_CONTAINMENT_EXPORTS = frozenset({
    "MemoryCircuit", "CircuitOpen", "quarantine_topic", "is_quarantined", "safe_recall",
    "containment_health",
})

__all__ = [
    "MemoryEngine", "Fact", "HealthReport", "EngineConfig", "DEFAULT_STORE_PATH",
    "MemoryEngineError", "ConfigurationError", "ValidationError", "EpistemicStatusError",
    "EventTimeError", "GroundedWriteRefused", "IndexDriftError", "StoreUnavailableError",
    "NotFoundError", "DependencyUnavailableError", "TransientError", "RetryPolicy",
    "call_with_retry", "idempotency_key", "EPISTEMIC_STATUSES", "UNLABELED",
    *sorted(_ENGINE_EXPORTS),
    *sorted(_PREDICTIVE_EXPORTS),
    *sorted(_TEMPORAL_EXPORTS),
    *sorted(_EPISODIC_EXPORTS),
    *sorted(_INGEST_EXPORTS),
    *sorted(_SKILLS_EXPORTS),
    *sorted(_SEARCH_EXPORTS),
    *sorted(_SESSION_EXPORTS),
    *sorted(_VERIFY_EXPORTS),
    *sorted(_CONTAINMENT_EXPORTS),
    *sorted(_FORGETTING_EXPORTS),
    *sorted(_WORKING_EXPORTS),
    *sorted(_CONSOLIDATE_EXPORTS),
    "__version__",
]


def __getattr__(name: str) -> Any:
    if name in _ENGINE_EXPORTS:
        from . import memory as _engine
        try:
            return getattr(_engine, name)
        except AttributeError as exc:
            raise AttributeError(
                f"memory_engine declares {name!r} but memory does not define it"
            ) from exc
    if name in _PREDICTIVE_EXPORTS:
        from . import predictive as m; return getattr(m, name)
    if name in _TEMPORAL_EXPORTS:
        from . import temporal as m; return getattr(m, name)
    if name in _EPISODIC_EXPORTS:
        from . import episodic as m; return getattr(m, name)
    if name in _INGEST_EXPORTS:
        from . import ingest as m; return getattr(m, name)
    if name in _SKILLS_EXPORTS:
        from . import skills as m; return getattr(m, name)
    if name in _SEARCH_EXPORTS:
        from . import search as m; return getattr(m, name)
    if name in _SESSION_EXPORTS:
        from . import session as m; return getattr(m, name)
    if name in _VERIFY_EXPORTS:
        from . import verify as m; return getattr(m, name)
    if name in _CONTAINMENT_EXPORTS:
        from . import containment as m; return getattr(m, name)
    if name in _FORGETTING_EXPORTS:
        from . import forgetting as m; return getattr(m, name)
    if name in _WORKING_EXPORTS:
        from . import working as m; return getattr(m, name)
    if name in _CONSOLIDATE_EXPORTS:
        from . import consolidate as m; return getattr(m, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
