"""Pluggable vector backends for mem20 memory engine.

This package provides the VectorBackend ABC and built-in backend implementations.

Available backends (register via entry-points or explicitly):
- faiss: FAISS-based indexes (Flat, IVF, HNSW)
- memory: In-memory backend for testing (flat or hnsw)
- pgvector: PostgreSQL pgvector extension (future)
- qdrant: Qdrant vector database (future)
- lancedb: LanceDB embedded columnar store (future)
- milvus: Milvus distributed vector database (future)
- weaviate: Weaviate vector database (future)

Usage:
    from memory_engine.backends import registry, BackendConfig

    config = BackendConfig(backend="faiss", dimension=768)
    backend = registry.create(config)
    await backend.initialize(config)
    await backend.add([...])
    results = await backend.search(...)
"""

from memory_engine.backends.base import (
    BackendConfig,
    IndexStats,
    SearchQuery,
    SearchResult,
    VectorBackend,
    VectorRecord,
)
from memory_engine.backends.registry import BackendRegistry, registry

__all__ = [
    "BackendConfig",
    "VectorBackend",
    "VectorRecord",
    "SearchQuery",
    "SearchResult",
    "IndexStats",
    "BackendRegistry",
    "registry",
]

# Import built-in backends to trigger registration
from memory_engine.backends import memory_backend  # noqa: F401
from memory_engine.backends import faiss_backend  # noqa: F401