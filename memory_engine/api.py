"""Typed public facade over the memory engine.

Why this module exists
----------------------
``memory_engine.memory`` is a 4,800-line module of free functions with no
declared surface: no ``__all__``, no types on the return values, and errors
raised as bare builtins from arbitrary depth. Every consumer (the MCP server,
``gateway/``, four language SDKs, the benchmark harness) reaches into it
directly, so any internal rename is a breaking change nobody can detect.

``MemoryEngine`` is the seam. It is a thin, typed, documented object that:

* declares the supported operations and their exact return shapes,
* translates the engine's builtin exceptions into the typed error model in
  ``errors.py`` (while keeping the builtin base classes, so old handlers work),
* validates arguments at the boundary instead of 3,000 lines deep,
* exposes ``health()`` for a readiness probe.

It deliberately does NOT reimplement behaviour. Every method delegates to the
existing engine function, so there is exactly one implementation of the logic
and no drift between the facade and the engine.

Stability
---------
Everything exported from ``memory_engine`` (see ``__init__.py``) is the
supported surface. Anything reached via ``memory_engine.memory.<name>`` that is
not re-exported is internal and may change without notice.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from . import errors
from .config import EngineConfig

__all__ = ["MemoryEngine", "Fact", "HealthReport", "EPISTEMIC_STATUSES", "UNLABELED"]

# Mirrors memory_engine.memory.EPISTEMIC_STATUSES. Duplicated as a literal so
# the contract is readable without importing the 4,800-line module, and asserted
# equal to the engine's list in tests/test_contract.py so it cannot drift.
EPISTEMIC_STATUSES: tuple[str, ...] = (
    "observed",
    "inferred",
    "imagined",
    "user_stated",
    "hypothesis",
    "agent_generated",
)
UNLABELED = "unlabeled"


@dataclass(frozen=True)
class Fact:
    """A stored memory record, as returned by the read operations.

    The engine returns plain dicts. ``Fact`` is a typed *view* over one, not a
    replacement: ``Fact.from_record`` keeps the original dict in ``raw`` so a
    caller that needs a field this dataclass does not model can still reach it.
    """

    id: str
    topic: str
    content: str
    ts: str
    actor: str
    tags: tuple[str, ...]
    priority: str
    epistemic_status: str
    origin: str
    valid_from: str | None = None
    valid_to: str | None = None
    confidence: float | None = None
    source: str | None = None
    raw: Mapping[str, Any] | None = None

    @classmethod
    def from_record(cls, rec: Mapping[str, Any]) -> "Fact":
        return cls(
            id=str(rec.get("id", "")),
            topic=str(rec.get("topic", "")),
            content=str(rec.get("content", "")),
            ts=str(rec.get("ts", "")),
            actor=str(rec.get("actor", "")),
            tags=tuple(rec.get("tags") or ()),
            priority=str(rec.get("priority", "normal")),
            epistemic_status=str(rec.get("epistemic_status") or UNLABELED),
            origin=str(rec.get("origin", "grounded")),
            valid_from=rec.get("valid_from"),
            valid_to=rec.get("valid_to"),
            confidence=rec.get("confidence"),
            source=rec.get("source"),
            raw=rec,
        )

    @property
    def is_trusted(self) -> bool:
        """False for statuses the engine refuses to rely on without validation."""
        return self.epistemic_status not in {
            "imagined",
            "hypothesis",
            "agent_generated",
            UNLABELED,
        }


@dataclass(frozen=True)
class HealthReport:
    """Result of ``MemoryEngine.health()`` — suitable for a readiness probe."""

    healthy: bool
    store_path: str
    ledger_records: int
    indexes: Mapping[str, Any]
    config: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "store_path": self.store_path,
            "ledger_records": self.ledger_records,
            "indexes": dict(self.indexes),
            "config": dict(self.config),
        }


class MemoryEngine:
    """Typed facade over the Hermes tiered memory engine.

    Construction does not touch the store; the first operation does. That keeps
    ``MemoryEngine()`` cheap enough to build per request.

    The engine module resolves its store path at import time from
    ``MEM20_STORE_PATH``. If you need a non-default store, set the environment
    (or call ``EngineConfig.apply()``) BEFORE importing this package.
    """

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._engine = self._import_engine()
        if config is None:
            # Bind to the store the engine ACTUALLY resolved at import time,
            # not to a fresh read of os.environ. The engine caches its paths at
            # import; re-reading the environment here would let the facade
            # report one store while the engine writes to another.
            config = EngineConfig.from_env().with_store(self._engine.STORE_DIR)
        self._config = config

    # -- internals ----------------------------------------------------------

    @staticmethod
    def _import_engine():
        # Imported lazily so that constructing a config or importing the error
        # model does not drag in numpy/faiss/sentence-transformers.
        from . import memory as engine

        return engine

    def _translate(self, exc: BaseException) -> BaseException:
        """Map a builtin engine exception onto the typed model.

        Returns the exception to raise. Already-typed errors pass through
        untouched so a nested facade call does not re-wrap.
        """
        if isinstance(exc, errors.MemoryEngineError):
            return exc
        msg = str(exc)
        if isinstance(exc, PermissionError):
            return errors.GroundedWriteRefused(msg)
        if isinstance(exc, FileNotFoundError):
            return errors.StoreUnavailableError(msg)
        if isinstance(exc, ValueError):
            lowered = msg.lower()
            # Order matters: the engine raises bare ValueError for a missing
            # fact id too, so "not found" must be checked before the generic
            # validation fallback or a lookup miss is misreported as bad input.
            if "not found" in lowered:
                return errors.NotFoundError(msg)
            if "epistemic_status" in lowered:
                return errors.EpistemicStatusError(msg)
            if "event time" in lowered or "valid_from" in lowered:
                return errors.EventTimeError(msg)
            return errors.ValidationError(msg)
        if isinstance(exc, LookupError):
            return errors.NotFoundError(msg)
        if isinstance(exc, RuntimeError):
            if "drift" in msg.lower():
                return errors.IndexDriftError(msg)
            return errors.DependencyUnavailableError(msg)
        return exc

    def _call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 - re-raised below
            raise self._translate(exc) from exc

    # -- properties ---------------------------------------------------------

    @property
    def config(self) -> EngineConfig:
        return self._config

    @property
    def store_path(self) -> str:
        return str(self._config.store_path)

    # -- write surface ------------------------------------------------------

    def remember(
        self,
        topic: str,
        content: str,
        *,
        tags: Sequence[str] | None = None,
        priority: str = "normal",
        actor: str = "agent",
        epistemic_status: str | None = None,
        confidence: float | None = None,
        source: str | None = None,
        valid_from: str | None = None,
        valid_to: str | None = None,
    ) -> Fact:
        """Append a GROUNDED fact. ``epistemic_status`` is required.

        Raises ``EpistemicStatusError`` if the basis is undeclared — the engine
        refuses an unlabeled write rather than defaulting it.
        """
        self._require_text(topic, "topic")
        self._require_text(content, "content")
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise errors.ValidationError(
                f"confidence must be within [0, 1], got {confidence}",
                details={"confidence": confidence},
            )
        rec = self._call(
            self._engine.remember,
            topic,
            content,
            tags=list(tags) if tags is not None else None,
            priority=priority,
            actor=actor,
            valid_from=valid_from,
            valid_to=valid_to,
            confidence=confidence,
            epistemic_status=epistemic_status,
            source=source,
        )
        return Fact.from_record(rec)

    def remember_simulated(
        self,
        topic: str,
        content: str,
        *,
        tags: Sequence[str] | None = None,
        actor: str = "agent",
        scenario: str | None = None,
        sim_type: str = "imagination",
        ttl_days: int | None = None,
    ) -> Fact:
        """Write SIMULATED content into the separate partition.

        Never touches the grounded ledger or the retrieval indexes.
        """
        self._require_text(topic, "topic")
        self._require_text(content, "content")
        kwargs: dict[str, Any] = {
            "tags": list(tags) if tags is not None else None,
            "actor": actor,
            "scenario": scenario,
            "sim_type": sim_type,
        }
        if ttl_days is not None:
            kwargs["ttl_days"] = ttl_days
        rec = self._call(self._engine.remember_simulated, topic, content, **kwargs)
        return Fact.from_record(rec)

    def supersede(
        self,
        old_id: str,
        new_content: str,
        *,
        tags: Sequence[str] | None = None,
        actor: str = "agent",
        epistemic_status: str | None = None,
    ) -> Fact:
        """Replace a fact's content, preserving the old row for as-of reads."""
        self._require_text(old_id, "old_id")
        self._require_text(new_content, "new_content")
        rec = self._call(
            self._engine.supersede,
            old_id,
            new_content,
            tags=list(tags) if tags is not None else None,
            actor=actor,
            epistemic_status=epistemic_status,
        )
        return Fact.from_record(rec)

    # -- read surface -------------------------------------------------------

    def recall(
        self,
        *,
        topic: str | None = None,
        tags: Sequence[str] | None = None,
        k: int = 5,
        include_simulated: bool = False,
    ) -> list[Fact]:
        """Most-recent-first facts, optionally filtered by topic/tags."""
        self._require_k(k)
        recs = self._call(
            self._engine.recall,
            topic=topic,
            tags=list(tags) if tags is not None else None,
            k=k,
            include_simulated=include_simulated,
        )
        return [Fact.from_record(r) for r in recs]

    def recall_at(
        self,
        as_of: str | None = None,
        *,
        topic: str | None = None,
        tags: Sequence[str] | None = None,
        k: int = 5,
        include_simulated: bool = False,
    ) -> list[Fact]:
        """Bi-temporal read: what was true, and known, at ``as_of``."""
        self._require_k(k)
        recs = self._call(
            self._engine.recall_at,
            as_of=as_of,
            topic=topic,
            tags=list(tags) if tags is not None else None,
            k=k,
            include_simulated=include_simulated,
        )
        return [Fact.from_record(r) for r in recs]

    def recall_semantic(
        self,
        query: str,
        *,
        k: int = 5,
        topic: str | None = None,
        tags: Sequence[str] | None = None,
        strict: bool = False,
    ) -> list[Fact]:
        """Vector search. ``strict=True`` raises ``IndexDriftError`` on a stale index."""
        self._require_text(query, "query")
        self._require_k(k)
        recs = self._call(
            self._engine.recall_semantic,
            query,
            k=k,
            topic=topic,
            tags=list(tags) if tags is not None else None,
            strict=strict,
        )
        return [Fact.from_record(r) for r in recs]

    def recall_hybrid(
        self,
        query: str,
        *,
        k: int = 5,
        topic: str | None = None,
        tags: Sequence[str] | None = None,
        alpha: float = 0.5,
    ) -> list[Fact]:
        """Vector + BM25 fused search. ``alpha`` weights the vector half."""
        self._require_text(query, "query")
        self._require_k(k)
        if not 0.0 <= alpha <= 1.0:
            raise errors.ValidationError(
                f"alpha must be within [0, 1], got {alpha}", details={"alpha": alpha}
            )
        recs = self._call(
            self._engine.recall_hybrid,
            query,
            k=k,
            topic=topic,
            tags=list(tags) if tags is not None else None,
            alpha=alpha,
        )
        # The engine returns [{"error": ...}] when no search dependency is
        # installed. Surface that as a typed error instead of a fake result.
        if recs and isinstance(recs[0], Mapping) and "error" in recs[0]:
            raise errors.DependencyUnavailableError(str(recs[0]["error"]))
        return [Fact.from_record(r) for r in recs]

    # -- operations ---------------------------------------------------------

    def rebuild_index(self) -> str:
        """Re-derive the deep-store index from the ledger."""
        return self._call(self._engine.rebuild_index)

    def index_health(self) -> dict[str, Any]:
        """Per-index drift report. Never raises for a missing index."""
        return self._call(self._engine.index_health)

    def status(self) -> str:
        """Human-readable store summary (caps, counts, last event)."""
        return self._call(self._engine.status)

    def health(self) -> HealthReport:
        """Readiness probe: is the store present and are the indexes consistent?

        A missing store is reported as unhealthy rather than raised, because a
        readiness endpoint must answer, not crash.
        """
        store = self._config.store_path
        if not store.exists():
            return HealthReport(
                healthy=False,
                store_path=str(store),
                ledger_records=0,
                indexes={},
                config=self._config.describe(),
            )
        try:
            idx = self.index_health()
        except errors.MemoryEngineError as exc:
            return HealthReport(
                healthy=False,
                store_path=str(store),
                ledger_records=0,
                indexes={"error": exc.to_dict()},
                config=self._config.describe(),
            )
        return HealthReport(
            healthy=bool(idx.get("healthy")),
            store_path=str(store),
            ledger_records=int(idx.get("ledger_records", 0)),
            indexes=idx.get("indexes", {}),
            config=self._config.describe(),
        )

    # -- validation helpers -------------------------------------------------

    @staticmethod
    def _require_text(value: Any, name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise errors.ValidationError(
                f"{name} must be a non-empty string, got {value!r}",
                details={"argument": name},
            )

    @staticmethod
    def _require_k(k: Any) -> None:
        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
            raise errors.ValidationError(
                f"k must be a positive integer, got {k!r}", details={"k": k}
            )
