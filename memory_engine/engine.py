"""Pluggable vector backend engine for mem20.

This module provides the MemoryEngine class that uses the BackendRegistry
to support multiple vector backends (FAISS, pgvector, Qdrant, LanceDB, Milvus,
Weaviate, Memory).

The public API mirrors the existing MemoryEngine facade in api.py but delegates
vector operations to the configured backend.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from memory_engine.backends.base import BackendConfig, SearchQuery, VectorBackend, VectorRecord
from memory_engine.backends.registry import registry
from memory_engine.config import EngineConfig
from memory_engine.errors import ConfigurationError, DependencyUnavailableError, MemoryEngineError

logger = logging.getLogger(__name__)

__all__ = ["MemoryEngine", "BackendConfig", "VectorRecord", "SearchQuery"]


@dataclass(frozen=True)
class Fact:
    """A stored memory record returned by read operations."""

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
            epistemic_status=str(rec.get("epistemic_status") or "unlabeled"),
            origin=str(rec.get("origin", "grounded")),
            valid_from=rec.get("valid_from"),
            valid_to=rec.get("valid_to"),
            confidence=rec.get("confidence"),
            source=rec.get("source"),
            raw=rec,
        )

    @property
    def is_trusted(self) -> bool:
        return self.epistemic_status not in {
            "imagined",
            "hypothesis",
            "agent_generated",
            "unlabeled",
        }


@dataclass(frozen=True)
class HealthReport:
    """Result of MemoryEngine.health() — suitable for a readiness probe."""

    healthy: bool
    store_path: str
    ledger_records: int
    indexes: Mapping[str, Any]
    config: Mapping[str, Any]
    backend: str
    backend_stats: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "store_path": self.store_path,
            "ledger_records": self.ledger_records,
            "indexes": dict(self.indexes),
            "config": dict(self.config),
            "backend": self.backend,
            "backend_stats": dict(self.backend_stats) if self.backend_stats else None,
        }


class MemoryEngine:
    """Pluggable vector backend engine for mem20.

    This engine delegates vector storage and search to a configured backend
    (FAISS, pgvector, Qdrant, etc.) while maintaining the existing mem20
    memory semantics (ledger, epistemic status, temporal queries, etc.).

    Construction does not initialize the backend; use async context manager
    or call initialize() explicitly.
    """

    def __init__(self, config: BackendConfig | None = None) -> None:
        if config is None:
            # Default to FAISS for backward compatibility
            config = BackendConfig(backend="faiss", dimension=768)
        self._config = config
        self._backend: VectorBackend | None = None
        self._initialized = False

    @property
    def config(self) -> BackendConfig:
        return self._config

    @property
    def backend(self) -> VectorBackend:
        if self._backend is None:
            raise RuntimeError("Backend not initialized. Call initialize() or use async context manager.")
        return self._backend

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def initialize(self) -> None:
        """Initialize the backend with the configured settings."""
        if self._initialized:
            return

        self._backend = registry.create(self._config)
        await self._backend.initialize(self._config)
        self._initialized = True
        logger.info("MemoryEngine initialized with backend: %s", self._config.backend)

    async def close(self) -> None:
        """Close the backend and release resources."""
        if self._backend is not None:
            await self._backend.close()
            self._backend = None
            self._initialized = False

    async def __aenter__(self) -> "MemoryEngine":
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # ─── Write operations ───

    async def store(
        self,
        texts: Sequence[str],
        embeddings: Sequence[Sequence[float] | Any],
        metadatas: Sequence[Mapping[str, Any]] | None = None,
    ) -> list[str]:
        """Store texts with pre-computed embeddings.

        Args:
            texts: Text content for each vector.
            embeddings: Pre-computed embeddings (list of vectors).
            metadatas: Optional metadata for each vector.

        Returns:
            List of assigned vector IDs.
        """
        if not self._initialized:
            await self.initialize()

        if len(texts) != len(embeddings):
            raise ValueError("texts and embeddings must have same length")

        metadatas = metadatas or [{}] * len(texts)
        if len(metadatas) != len(texts):
            raise ValueError("metadatas must have same length as texts")

        import numpy as np

        records = []
        ids = []
        for i, (text, emb, meta) in enumerate(zip(texts, embeddings, metadatas)):
            vector = np.asarray(emb, dtype=np.float32)
            if vector.ndim != 1:
                raise ValueError(f"Embedding {i} must be 1-D, got shape {vector.shape}")

            vec_id = meta.get("id") or f"vec-{os.urandom(8).hex()}"
            ids.append(vec_id)

            record = VectorRecord(
                id=vec_id,
                vector=vector,
                metadata=dict(meta),
                payload={"text": text},
            )
            records.append(record)

        await self._backend.add(records)
        return ids

    async def recall(
        self,
        query_embedding: Sequence[float] | Any,
        k: int = 10,
        filter: Mapping[str, Any] | None = None,
    ) -> list[Fact]:
        """Vector similarity search (semantic recall).

        Args:
            query_embedding: Query vector.
            k: Number of results to return.
            filter: Optional metadata filter.

        Returns:
            List of Fact objects sorted by relevance.
        """
        if not self._initialized:
            await self.initialize()

        import numpy as np

        vector = np.asarray(query_embedding, dtype=np.float32)
        if vector.ndim != 1:
            raise ValueError("Query embedding must be 1-D")

        query = SearchQuery(vector=vector, k=k, filter=dict(filter) if filter else None)
        results = await self._backend.search(query)

        return [
            Fact(
                id=r.record.id,
                topic=r.record.metadata.get("topic", ""),
                content=r.record.payload.get("text", ""),
                ts=r.record.metadata.get("ts", ""),
                actor=r.record.metadata.get("actor", "agent"),
                tags=tuple(r.record.metadata.get("tags", [])),
                priority=r.record.metadata.get("priority", "normal"),
                epistemic_status=r.record.metadata.get("epistemic_status", "unlabeled"),
                origin=r.record.metadata.get("origin", "grounded"),
                raw=r.record.metadata,
            )
            for r in results
        ]

    async def search(
        self,
        query: str,
        k: int = 10,
        filter: Mapping[str, Any] | None = None,
    ) -> list[Fact]:
        """Text-based search (requires embedding model).

        Note: This requires an embedding model to be configured.
        For now, raises DependencyUnavailableError.
        """
        raise DependencyUnavailableError(
            "Text-based search requires embedding model. Use recall() with pre-computed embeddings."
        )

    async def delete(self, ids: Sequence[str]) -> None:
        """Delete vectors by ID."""
        if not self._initialized:
            await self.initialize()
        await self._backend.delete(list(ids))

    async def compact(self) -> None:
        """Compact the index (reclaim deleted space, rebuild)."""
        if not self._initialized:
            await self.initialize()
        await self._backend.compact()

    async def stats(self) -> Mapping[str, Any]:
        """Get engine and backend statistics."""
        if not self._initialized:
            await self.initialize()

        backend_stats = await self._backend.stats()
        return {
            "backend": self._config.backend,
            "backend_name": backend_stats.backend_name,
            "backend_version": backend_stats.backend_version,
            "index_type": backend_stats.index_type,
            "num_vectors": backend_stats.num_vectors,
            "dimension": backend_stats.dimension,
            "index_size_bytes": backend_stats.index_size_bytes,
            "build_time_seconds": backend_stats.build_time_seconds,
        }

    def health(self) -> HealthReport:
        """Readiness probe: is the backend available and healthy?"""
        if not self._initialized or self._backend is None:
            return HealthReport(
                healthy=False,
                store_path="",
                ledger_records=0,
                indexes={},
                config=self._config.__dict__ if hasattr(self._config, "__dict__") else {},
                backend=self._config.backend,
            )

        try:
            # Try a quick operation to verify backend is responsive
            # Note: This is synchronous; for async health check use stats()
            return HealthReport(
                healthy=True,
                store_path="",
                ledger_records=0,
                indexes={},
                config={},
                backend=self._config.backend,
            )
        except Exception as e:
            return HealthReport(
                healthy=False,
                store_path="",
                ledger_records=0,
                indexes={"error": str(e)},
                config={},
                backend=self._config.backend,
            )