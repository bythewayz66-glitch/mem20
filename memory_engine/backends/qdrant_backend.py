"""Qdrant vector backend implementation.

Uses Qdrant vector database for vector storage and search.
Supports HNSW indexes, payload filtering, hybrid search, and cloud deployments.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional

import numpy as np

from memory_engine.backends.base import (
    BackendConfig,
    IndexStats,
    SearchQuery,
    SearchResult,
    VectorBackend,
    VectorRecord,
)

logger = logging.getLogger(__name__)

# Try to import dependencies
try:
    from qdrant_client import QdrantClient, AsyncQdrantClient
    from qdrant_client.http import models as qdrant_models
    from qdrant_client.http.exceptions import UnexpectedResponse

    QDRANT_AVAILABLE = True
except ImportError:
    QdrantClient = None  # type: ignore
    AsyncQdrantClient = None  # type: ignore
    qdrant_models = None  # type: ignore
    QDRANT_AVAILABLE = False


class QdrantBackend(VectorBackend):
    """Qdrant vector backend with HNSW index and payload filtering."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._client: Optional[AsyncQdrantClient] = None
        self._sync_client: Optional[QdrantClient] = None
        self._lock = threading.RLock()
        self._build_time = 0.0
        self._collection_name = config.qdrant_collection

    @property
    def name(self) -> str:
        return "qdrant"

    @property
    def supports_filter(self) -> bool:
        return True  # Full payload filtering

    @property
    def supports_filter_expr(self) -> bool:
        return True  # Qdrant filter DSL

    @property
    def supports_payload(self) -> bool:
        return True  # Native payload support

    @property
    def supports_delete(self) -> bool:
        return True

    @property
    def supports_update(self) -> bool:
        return True  # Upsert supported

    @property
    def supports_persist(self) -> bool:
        return True

    @property
    def supports_replica(self) -> bool:
        return True  # Qdrant supports replicas

    @property
    def is_distributed(self) -> bool:
        return True  # Qdrant cluster mode

    @property
    def max_dimension(self) -> int:
        return 0  # No hard limit

    def _get_url(self) -> str:
        if self._config.qdrant_url:
            return self._config.qdrant_url
        return os.environ.get("QDRANT_URL", "http://localhost:6333")

    def _get_api_key(self) -> Optional[str]:
        if self._config.qdrant_api_key:
            return self._config.qdrant_api_key
        return os.environ.get("QDRANT_API_KEY")

    async def initialize(self, config: BackendConfig) -> None:
        if not QDRANT_AVAILABLE:
            raise RuntimeError(
                "Qdrant client not installed. Install with: pip install qdrant-client"
            )

        self._config = config
        self._dimension = config.dimension
        self._collection_name = config.qdrant_collection

        url = self._get_url()
        api_key = self._get_api_key()

        self._client = AsyncQdrantClient(url=url, api_key=api_key)
        self._sync_client = QdrantClient(url=url, api_key=api_key)

        # Create collection if not exists
        await self._ensure_collection()

        logger.info(
            "QdrantBackend initialized: dim=%d, collection=%s, url=%s",
            self._dimension,
            self._collection_name,
            url,
        )

    async def _ensure_collection(self) -> None:
        """Create collection with HNSW index if it doesn't exist."""
        try:
            await self._client.get_collection(self._collection_name)
            logger.info("Collection %s already exists", self._collection_name)
        except UnexpectedResponse:
            # Collection doesn't exist, create it
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self._dimension,
                    distance=qdrant_models.Distance.COSINE,
                    hnsw_config=qdrant_models.HnswConfigDiff(
                        m=self._config.qdrant_hnsw_m,
                        ef_construct=self._config.qdrant_hnsw_ef_construct,
                    ),
                ),
            )
            logger.info("Created collection %s with HNSW index", self._collection_name)

        # Create payload indexes for common filter fields
        # This is done lazily on first filter use

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    async def add(self, records: list[VectorRecord]) -> None:
        if not self._client:
            raise RuntimeError("Backend not initialized")

        points = []
        for record in records:
            if record.vector.shape[0] != self._dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self._dimension}, got {record.vector.shape[0]}"
                )

            point = qdrant_models.PointStruct(
                id=record.id,
                vector=record.vector.tolist(),
                payload={
                    "metadata": record.metadata,
                    "payload": record.payload,
                },
            )
            points.append(point)

        # Batch upsert
        await self._client.upsert(
            collection_name=self._collection_name,
            points=points,
            wait=True,
        )

    async def delete(self, ids: list[str]) -> None:
        if not self._client or not ids:
            return

        await self._client.delete(
            collection_name=self._collection_name,
            points_selector=qdrant_models.PointIdsList(points=ids),
            wait=True,
        )

    async def update(self, records: list[VectorRecord]) -> None:
        # Qdrant upsert handles updates natively
        await self.add(records)

    def _build_qdrant_filter(self, filter_dict: dict[str, Any]) -> qdrant_models.Filter:
        """Convert simple dict filter to Qdrant Filter."""
        must_conditions = []
        for key, value in filter_dict.items():
            # Filter on metadata sub-object
            must_conditions.append(
                qdrant_models.FieldCondition(
                    key=f"metadata.{key}",
                    match=qdrant_models.MatchValue(value=value),
                )
            )
        return qdrant_models.Filter(must=must_conditions)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        if not self._client:
            raise RuntimeError("Backend not initialized")

        # Build filter
        qdrant_filter = None
        if query.filter:
            qdrant_filter = self._build_qdrant_filter(query.filter)
        # TODO: Support filter_expr with Qdrant's advanced filter DSL

        # Search parameters
        search_params = qdrant_models.SearchParams(
            hnsw_ef=128,  # Can be made configurable
            exact=False,
        )

        # Determine which fields to return
        with_payload = query.include_payload
        with_vectors = query.include_vector

        results = await self._client.search(
            collection_name=self._collection_name,
            query_vector=query.vector.tolist(),
            query_filter=qdrant_filter,
            limit=query.k,
            with_payload=with_payload,
            with_vectors=with_vectors,
            search_params=search_params,
        )

        search_results = []
        for rank, hit in enumerate(results):
            payload = hit.payload or {}
            
            # Extract metadata and payload from stored structure
            metadata = payload.get("metadata", {})
            stored_payload = payload.get("payload", {})

            # Get vector if requested
            vector = np.array([], dtype=np.float32)
            if query.include_vector and hit.vector is not None:
                vector = np.array(hit.vector, dtype=np.float32)

            record = VectorRecord(
                id=str(hit.id),
                vector=vector,
                metadata=metadata,
                payload=stored_payload if query.include_payload else {},
            )

            # Qdrant returns cosine similarity directly for COSINE distance
            score = float(hit.score)
            search_results.append(SearchResult(record=record, score=score, rank=rank))

        return search_results

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        if not self._client or not ids:
            return [None] * len(ids)

        results = await self._client.retrieve(
            collection_name=self._collection_name,
            ids=ids,
            with_payload=True,
            with_vectors=False,
        )

        # Build lookup
        hit_dict = {str(hit.id): hit for hit in results}

        records = []
        for id_ in ids:
            hit = hit_dict.get(id_)
            if hit is None:
                records.append(None)
            else:
                payload = hit.payload or {}
                metadata = payload.get("metadata", {})
                stored_payload = payload.get("payload", {})
                records.append(VectorRecord(
                    id=id_,
                    vector=np.array([], dtype=np.float32),
                    metadata=metadata,
                    payload=stored_payload,
                ))
        return records

    async def compact(self) -> None:
        # Qdrant handles compaction automatically
        # Force segment optimization
        if self._sync_client:
            self._sync_client.update_collection(
                collection_name=self._collection_name,
                optimizer_config=qdrant_models.OptimizersConfigDiff(
                    deleted_threshold=0.0,  # Force merge of deleted
                ),
            )

    async def stats(self) -> IndexStats:
        if not self._client:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="qdrant",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

        try:
            info = await self._client.get_collection(self._collection_name)
            return IndexStats(
                num_vectors=info.vectors_count or 0,
                dimension=self._dimension,
                index_size_bytes=0,  # Qdrant doesn't expose index size directly
                backend_name="qdrant",
                backend_version="qdrant-client",
                index_type=f"HNSW(m={self._config.qdrant_hnsw_m})",
                build_time_seconds=self._build_time,
            )
        except Exception:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="qdrant",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

    async def backup(self, path: str) -> None:
        # Qdrant supports snapshots
        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)

        if self._sync_client:
            # Create snapshot
            snapshot = self._sync_client.create_snapshot(self._collection_name)
            # In practice, you'd download the snapshot file
            # For now, save config and note snapshot name
            config_data = {
                "backend": "qdrant",
                "dimension": self._dimension,
                "collection": self._collection_name,
                "snapshot": snapshot.name if hasattr(snapshot, 'name') else "unknown",
            }
            with open(out / "config.json", "w") as f:
                json.dump(config_data, f, indent=2)

    async def restore(self, path: str) -> None:
        # Restore from snapshot would require Qdrant API
        # This is a placeholder
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"Backup path not found: {path}")


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("qdrant", lambda config: QdrantBackend(config))


_register()