"""VectorBackend abstract base class and core dataclasses.

This module defines the pluggable backend interface for the mem20 memory engine.
All vector backends (FAISS, pgvector, Qdrant, LanceDB, Milvus, Weaviate, Memory)
must implement the VectorBackend ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
import numpy as np


@dataclass(frozen=True, slots=True)
class VectorRecord:
    """A single vector with metadata and optional payload.

    Attributes:
        id: Unique identifier (user-provided or UUID).
        vector: Dense embedding vector, shape (dim,), dtype float32.
        metadata: Filterable key-value fields (tenant, tags, timestamps, etc.).
        payload: Opaque data returned on recall (text, blobs, JSON).
    """
    id: str
    vector: np.ndarray
    metadata: dict[str, Any]
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if self.vector.dtype != np.float32:
            object.__setattr__(self, "vector", self.vector.astype(np.float32, copy=False))
        if self.vector.ndim != 1:
            raise ValueError(f"vector must be 1-D, got shape {self.vector.shape}")


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """Parameters for a vector search request.

    Attributes:
        vector: Query vector, shape (dim,), dtype float32.
        k: Number of nearest neighbors to return.
        filter: Exact-match filter on metadata fields (e.g., {"tenant": "acme"}).
        filter_expr: Backend-specific filter expression (SQL WHERE, Lucene, etc.).
        include_payload: Whether to include payload in results.
        include_vector: Whether to include vector in results.
    """
    vector: np.ndarray
    k: int = 10
    filter: Optional[dict[str, Any]] = None
    filter_expr: Optional[str] = None
    include_payload: bool = True
    include_vector: bool = False

    def __post_init__(self) -> None:
        if self.vector.dtype != np.float32:
            object.__setattr__(self, "vector", self.vector.astype(np.float32, copy=False))
        if self.vector.ndim != 1:
            raise ValueError(f"vector must be 1-D, got shape {self.vector.shape}")
        if self.k <= 0:
            raise ValueError("k must be positive")


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A single search result.

    Attributes:
        record: The matched VectorRecord (payload/vector per query flags).
        score: Similarity score in [0, 1] (1 = identical for cosine).
        rank: Zero-based rank in result set.
    """
    record: VectorRecord
    score: float
    rank: int


@dataclass(frozen=True, slots=True)
class IndexStats:
    """Current index statistics.

    Attributes:
        num_vectors: Total vectors in index.
        dimension: Vector dimension.
        index_size_bytes: On-disk/in-memory index size.
        backend_name: Backend identifier (e.g., "faiss", "qdrant").
        backend_version: Backend library version.
        index_type: Index algorithm (e.g., "HNSW32", "IVF_PQ", "DiskANN").
        build_time_seconds: Time to build current index.
    """
    num_vectors: int
    dimension: int
    index_size_bytes: int
    backend_name: str
    backend_version: str
    index_type: str
    build_time_seconds: float


@dataclass(frozen=True, slots=True)
class BackendConfig:
    """Configuration for a vector backend.

    All backends share common fields; backend-specific fields are prefixed.
    Unknown fields are stored in `extra` for forward compatibility.
    """
    backend: str
    dimension: int

    # FAISS-specific
    faiss_index_type: str = "HNSW32"
    faiss_metric: str = "cosine"
    faiss_nprobe: int = 16
    faiss_ef_search: int = 64
    faiss_ef_construction: int = 128

    # pgvector-specific
    pgvector_dsn: Optional[str] = None
    pgvector_table: str = "vectors"
    pgvector_hnsw_m: int = 16
    pgvector_hnsw_ef_construction: int = 64

    # Qdrant-specific
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    qdrant_collection: str = "mem20"
    qdrant_hnsw_m: int = 16
    qdrant_hnsw_ef_construct: int = 100

    # LanceDB-specific
    lancedb_uri: str = "~/.mem20/lancedb"
    lancedb_table: str = "vectors"
    lancedb_index_type: str = "IVF_PQ"

    # Milvus-specific
    milvus_uri: Optional[str] = None
    milvus_token: Optional[str] = None
    milvus_collection: str = "mem20"
    milvus_index_type: str = "HNSW"
    milvus_metric_type: str = "COSINE"

    # Weaviate-specific
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None
    weaviate_class: str = "Mem20Vector"
    weaviate_vectorizer: str = "none"

    # Memory (in-memory, for testing)
    memory_backend: str = "flat"

    # Common
    batch_size: int = 1024
    num_threads: int = 0
    cache_size_gb: float = 0.0

    # Extensibility
    extra: dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.extra is None:
            object.__setattr__(self, "extra", {})


class VectorBackend(ABC):
    """Abstract base class for all vector backends.

    Implementations must be thread-safe for concurrent read/write.
    All async methods should use asyncio-compatible I/O.
    """

    # ─── Capability flags (static, no I/O) ───

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend identifier (e.g., 'faiss', 'qdrant', 'memory')."""

    @property
    @abstractmethod
    def supports_filter(self) -> bool:
        """Supports exact-match metadata filtering via `SearchQuery.filter`."""

    @property
    @abstractmethod
    def supports_filter_expr(self) -> bool:
        """Supports backend-specific filter expressions via `SearchQuery.filter_expr`."""

    @property
    @abstractmethod
    def supports_payload(self) -> bool:
        """Supports storing/retrieving opaque payload data."""

    @property
    @abstractmethod
    def supports_delete(self) -> bool:
        """Supports deleting vectors by ID (soft or hard)."""

    @property
    @abstractmethod
    def supports_update(self) -> bool:
        """Supports updating existing vectors (full record replacement)."""

    @property
    @abstractmethod
    def supports_persist(self) -> bool:
        """Supports persisting index to disk and restoring."""

    @property
    @abstractmethod
    def supports_replica(self) -> bool:
        """Supports read replicas / follower nodes."""

    @property
    @abstractmethod
    def is_distributed(self) -> bool:
        """True if backend can run as a distributed cluster."""

    @property
    @abstractmethod
    def max_dimension(self) -> int:
        """Maximum supported vector dimension (0 = unlimited)."""

    # ─── Lifecycle ───

    @abstractmethod
    async def initialize(self, config: BackendConfig) -> None:
        """Create index, connect to service, validate schema.

        Args:
            config: Backend-specific configuration.

        Raises:
            ValueError: If config is invalid for this backend.
            ConnectionError: If unable to connect to backend service.
        """

    @abstractmethod
    async def close(self) -> None:
        """Flush buffers, release connections, cleanup temp files.

        Must be idempotent (safe to call multiple times).
        """

    # ─── Write path ───

    @abstractmethod
    async def add(self, records: list[VectorRecord]) -> None:
        """Batch insert vectors. Must be idempotent on ID conflict (upsert semantics).

        Args:
            records: List of VectorRecord to add. All vectors must match configured dimension.

        Raises:
            ValueError: If dimension mismatch or invalid records.
        """

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID.

        Args:
            ids: List of vector IDs to delete. Missing IDs are ignored.

        Note:
            Default implementation may be soft delete (mark tombstone).
            Hard delete requires `compact()`.
        """

    @abstractmethod
    async def update(self, records: list[VectorRecord]) -> None:
        """Update existing vectors (full record replacement).

        Args:
            records: List of VectorRecord with existing IDs.

        Default:
            Implemented as `delete(ids)` + `add(records)` if not natively supported.
        """

    # ─── Read path ───

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Approximate nearest neighbor search with optional filtering.

        Args:
            query: Search parameters including vector, k, filters.

        Returns:
            List of SearchResult sorted by score descending (best first).
            Length <= query.k.

        Raises:
            ValueError: If query vector dimension mismatch.
        """

    @abstractmethod
    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        """Exact lookup by ID.

        Args:
            ids: List of vector IDs to retrieve.

        Returns:
            List of VectorRecord or None for each ID (same order as input).
        """

    # ─── Maintenance ───

    @abstractmethod
    async def compact(self) -> None:
        """Merge segments, reclaim deleted space, rebuild index.

        Should be called periodically after many deletes/updates.
        """

    @abstractmethod
    async def stats(self) -> IndexStats:
        """Return current index statistics."""

    @abstractmethod
    async def backup(self, path: str) -> None:
        """Export index + metadata to portable format at `path`.

        Format: directory with Parquet vectors + JSON metadata.
        """

    @abstractmethod
    async def restore(self, path: str) -> None:
        """Import index from backup at `path`. Replaces current index."""