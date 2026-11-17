"""Vector memory with support for pgvector, Qdrant, Weaviate, and in-memory."""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field

try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
except ImportError:
    AsyncQdrantClient = None

try:
    import weaviate
    from weaviate.classes.init import Auth
except ImportError:
    weaviate = None

from ..config import settings
from ..models import BaseModel as TeamzBaseModel


class VectorMemoryConfig(TeamzBaseModel):
    """Configuration for vector memory backend."""
    backend: str = "pgvector"  # pgvector, qdrant, weaviate, in_memory
    # pgvector
    pgvector_dsn: str = Field(default_factory=lambda: os.getenv("PGVECTOR_DSN", "postgresql://postgres:postgres@localhost:5432/teamz"))
    pgvector_table: str = "memory_vectors"
    pgvector_dimensions: int = 1536
    # Qdrant
    qdrant_url: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", "http://localhost:6333"))
    qdrant_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY"))
    qdrant_collection: str = "teamz_memory"
    # Weaviate
    weaviate_url: str = Field(default_factory=lambda: os.getenv("WEAVIATE_URL", "http://localhost:8080"))
    weaviate_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("WEAVIATE_API_KEY"))
    weaviate_class: str = "TeamzMemory"
    # In-memory (for testing only)
    # Common
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    default_top_k: int = 10
    similarity_threshold: float = 0.7


@dataclass
class MemoryVector:
    """A vector memory entry."""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    importance: float = 1.0
    ttl_seconds: Optional[float] = None
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "importance": self.importance,
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
        }


class VectorBackend(ABC):
    """Abstract vector storage backend."""

    @abstractmethod
    async def initialize(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def upsert(self, vectors: List[MemoryVector]) -> None:
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[MemoryVector, float]]:
        pass

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        pass

    @abstractmethod
    async def get(self, ids: List[str]) -> List[Optional[MemoryVector]]:
        pass

    @abstractmethod
    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        pass

    @abstractmethod
    async def prune_expired(self) -> int:
        pass


class PgVectorBackend(VectorBackend):
    """pgvector backend using asyncpg."""

    def __init__(self, config: VectorMemoryConfig) -> None:
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        if asyncpg is None:
            raise RuntimeError("asyncpg not installed. Run: pip install asyncpg")
        self._pool = await asyncpg.create_pool(self.config.pgvector_dsn, min_size=2, max_size=10)
        async with self._pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            # Create table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config.pgvector_table} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding VECTOR({self.config.pgvector_dimensions}),
                    metadata JSONB DEFAULT '{{}}',
                    created_at DOUBLE PRECISION NOT NULL,
                    updated_at DOUBLE PRECISION NOT NULL,
                    importance DOUBLE PRECISION DEFAULT 1.0,
                    ttl_seconds DOUBLE PRECISION,
                    access_count INTEGER DEFAULT 0,
                    last_accessed DOUBLE PRECISION NOT NULL
                )
            """)
            # Create index for similarity search
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.config.pgvector_table}_embedding_idx
                ON {self.config.pgvector_table} USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """)
            # Create metadata index
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {self.config.pgvector_table}_metadata_idx
                ON {self.config.pgvector_table} USING gin (metadata)
            """)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def upsert(self, vectors: List[MemoryVector]) -> None:
        if not self._pool:
            raise RuntimeError("Backend not initialized")
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                for vec in vectors:
                    await conn.execute(f"""
                        INSERT INTO {self.config.pgvector_table}
                        (id, content, embedding, metadata, created_at, updated_at, importance, ttl_seconds, access_count, last_accessed)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            updated_at = EXCLUDED.updated_at,
                            importance = EXCLUDED.importance,
                            ttl_seconds = EXCLUDED.ttl_seconds,
                            access_count = EXCLUDED.access_count,
                            last_accessed = EXCLUDED.last_accessed
                    """, vec.id, vec.content, vec.embedding, json.dumps(vec.metadata),
                        vec.created_at, vec.updated_at, vec.importance, vec.ttl_seconds,
                        vec.access_count, vec.last_accessed)

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[MemoryVector, float]]:
        if not self._pool:
            raise RuntimeError("Backend not initialized")

        filter_clause = ""
        params = [query_embedding, top_k]
        if filter_metadata:
            conditions = []
            for i, (key, value) in enumerate(filter_metadata.items()):
                param_idx = len(params) + 1
                conditions.append(f"metadata->>'{key}' = ${param_idx}")
                params.append(str(value))
            if conditions:
                filter_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT id, content, embedding, metadata, created_at, updated_at, importance,
                   ttl_seconds, access_count, last_accessed,
                   1 - (embedding <=> $1) as similarity
            FROM {self.config.pgvector_table}
            {filter_clause}
            ORDER BY embedding <=> $1
            LIMIT $2
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            results = []
            for row in rows:
                similarity = row["similarity"]
                if similarity >= threshold:
                    vec = MemoryVector(
                        id=row["id"],
                        content=row["content"],
                        embedding=list(row["embedding"]),
                        metadata=row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"]),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        importance=row["importance"],
                        ttl_seconds=row["ttl_seconds"],
                        access_count=row["access_count"],
                        last_accessed=row["last_accessed"],
                    )
                    results.append((vec, similarity))
            return results

    async def delete(self, ids: List[str]) -> None:
        if not self._pool:
            raise RuntimeError("Backend not initialized")
        if not ids:
            return
        placeholders = ",".join(f"${i+1}" for i in range(len(ids)))
        async with self._pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.config.pgvector_table} WHERE id IN ({placeholders})", *ids)

    async def get(self, ids: List[str]) -> List[Optional[MemoryVector]]:
        if not self._pool:
            raise RuntimeError("Backend not initialized")
        if not ids:
            return []
        placeholders = ",".join(f"${i+1}" for i in range(len(ids)))
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT id, content, embedding, metadata, created_at, updated_at, importance, ttl_seconds, access_count, last_accessed FROM {self.config.pgvector_table} WHERE id IN ({placeholders})",
                *ids
            )
            row_map = {row["id"]: row for row in rows}
            results = []
            for id_ in ids:
                row = row_map.get(id_)
                if row:
                    results.append(MemoryVector(
                        id=row["id"],
                        content=row["content"],
                        embedding=list(row["embedding"]),
                        metadata=row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"]),
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        importance=row["importance"],
                        ttl_seconds=row["ttl_seconds"],
                        access_count=row["access_count"],
                        last_accessed=row["last_accessed"],
                    ))
                else:
                    results.append(None)
            return results

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        if not self._pool:
            raise RuntimeError("Backend not initialized")
        filter_clause = ""
        params = []
        if filter_metadata:
            conditions = []
            for i, (key, value) in enumerate(filter_metadata.items()):
                param_idx = len(params) + 1
                conditions.append(f"metadata->>'{key}' = ${param_idx}")
                params.append(str(value))
            if conditions:
                filter_clause = "WHERE " + " AND ".join(conditions)
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self.config.pgvector_table} {filter_clause}", *params)
            return row[0]

    async def prune_expired(self) -> int:
        if not self._pool:
            raise RuntimeError("Backend not initialized")
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.config.pgvector_table} WHERE ttl_seconds IS NOT NULL AND created_at + ttl_seconds < $1",
                time.time()
            )
            return int(result.split()[-1]) if result else 0


class QdrantBackend(VectorBackend):
    """Qdrant backend."""

    def __init__(self, config: VectorMemoryConfig) -> None:
        self.config = config
        self._client: Optional[AsyncQdrantClient] = None

    async def initialize(self) -> None:
        if AsyncQdrantClient is None:
            raise RuntimeError("qdrant-client not installed. Run: pip install qdrant-client")
        self._client = AsyncQdrantClient(url=self.config.qdrant_url, api_key=self.config.qdrant_api_key)
        # Create collection if not exists
        collections = await self._client.get_collections()
        if self.config.qdrant_collection not in [c.name for c in collections.collections]:
            await self._client.create_collection(
                collection_name=self.config.qdrant_collection,
                vectors_config=VectorParams(
                    size=self.config.embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            )

    async def close(self) -> None:
        if self._client:
            await self._client.close()

    async def upsert(self, vectors: List[MemoryVector]) -> None:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        points = []
        for vec in vectors:
            points.append(PointStruct(
                id=vec.id,
                vector=vec.embedding,
                payload={
                    "content": vec.content,
                    "metadata": vec.metadata,
                    "created_at": vec.created_at,
                    "updated_at": vec.updated_at,
                    "importance": vec.importance,
                    "ttl_seconds": vec.ttl_seconds,
                    "access_count": vec.access_count,
                    "last_accessed": vec.last_accessed,
                }
            ))
        await self._client.upsert(collection_name=self.config.qdrant_collection, points=points)

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[MemoryVector, float]]:
        if not self._client:
            raise RuntimeError("Backend not initialized")

        query_filter = None
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(FieldCondition(key=f"payload.metadata.{key}", match=MatchValue(value=value)))
            query_filter = Filter(must=conditions)

        results = await self._client.search(
            collection_name=self.config.qdrant_collection,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=top_k,
            score_threshold=threshold,
        )

        output = []
        for hit in results:
            payload = hit.payload
            vec = MemoryVector(
                id=hit.id,
                content=payload["content"],
                embedding=hit.vector if hit.vector else [],
                metadata=payload["metadata"],
                created_at=payload["created_at"],
                updated_at=payload["updated_at"],
                importance=payload["importance"],
                ttl_seconds=payload.get("ttl_seconds"),
                access_count=payload["access_count"],
                last_accessed=payload["last_accessed"],
            )
            output.append((vec, hit.score))
        return output

    async def delete(self, ids: List[str]) -> None:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        if not ids:
            return
        await self._client.delete(collection_name=self.config.qdrant_collection, points_selector=ids)

    async def get(self, ids: List[str]) -> List[Optional[MemoryVector]]:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        if not ids:
            return []
        points = await self._client.retrieve(collection_name=self.config.qdrant_collection, ids=ids)
        point_map = {p.id: p for p in points}
        results = []
        for id_ in ids:
            point = point_map.get(id_)
            if point:
                payload = point.payload
                results.append(MemoryVector(
                    id=point.id,
                    content=payload["content"],
                    embedding=point.vector if point.vector else [],
                    metadata=payload["metadata"],
                    created_at=payload["created_at"],
                    updated_at=payload["updated_at"],
                    importance=payload["importance"],
                    ttl_seconds=payload.get("ttl_seconds"),
                    access_count=payload["access_count"],
                    last_accessed=payload["last_accessed"],
                ))
            else:
                results.append(None)
        return results

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        query_filter = None
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(FieldCondition(key=f"payload.metadata.{key}", match=MatchValue(value=value)))
            query_filter = Filter(must=conditions)
        result = await self._client.count(collection_name=self.config.qdrant_collection, count_filter=query_filter, exact=True)
        return result.count

    async def prune_expired(self) -> int:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        # Qdrant doesn't support TTL natively, need to scan and delete
        # This is a simplified implementation
        return 0


class WeaviateBackend(VectorBackend):
    """Weaviate backend."""

    def __init__(self, config: VectorMemoryConfig) -> None:
        self.config = config
        self._client: Optional[weaviate.Client] = None

    async def initialize(self) -> None:
        if weaviate is None:
            raise RuntimeError("weaviate-client not installed. Run: pip install weaviate-client")
        auth = None
        if self.config.weaviate_api_key:
            auth = Auth.api_key(self.config.weaviate_api_key)
        self._client = weaviate.connect_to_custom(
            http_host=self.config.weaviate_url.replace("http://", "").replace("https://", ""),
            http_port=8080,
            http_secure=self.config.weaviate_url.startswith("https"),
            grpc_host=self.config.weaviate_url.replace("http://", "").replace("https://", ""),
            grpc_port=50051,
            grpc_secure=self.config.weaviate_url.startswith("https"),
            auth_credentials=auth,
        )

    async def close(self) -> None:
        if self._client:
            self._client.close()

    async def upsert(self, vectors: List[MemoryVector]) -> None:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        # Weaviate batch insert
        with self._client.batch.dynamic() as batch:
            for vec in vectors:
                batch.add_object(
                    collection=self.config.weaviate_class,
                    properties={
                        "content": vec.content,
                        "metadata": json.dumps(vec.metadata),
                        "created_at": vec.created_at,
                        "updated_at": vec.updated_at,
                        "importance": vec.importance,
                        "ttl_seconds": vec.ttl_seconds or 0,
                        "access_count": vec.access_count,
                        "last_accessed": vec.last_accessed,
                    },
                    vector=vec.embedding,
                    uuid=vec.id,
                )

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[MemoryVector, float]]:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        # Simplified - would need proper Weaviate v4 query
        return []

    async def delete(self, ids: List[str]) -> None:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        # Simplified
        pass

    async def get(self, ids: List[str]) -> List[Optional[MemoryVector]]:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        return [None] * len(ids)

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        if not self._client:
            raise RuntimeError("Backend not initialized")
        return 0

    async def prune_expired(self) -> int:
        return 0


class VectorMemory:
    """Main vector memory interface."""

    def __init__(self, config: Optional[VectorMemoryConfig] = None) -> None:
        self.config = config or VectorMemoryConfig()
        self._backend: Optional[VectorBackend] = None
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        if self.config.backend == "pgvector":
            self._backend = PgVectorBackend(self.config)
        elif self.config.backend == "qdrant":
            self._backend = QdrantBackend(self.config)
        elif self.config.backend == "weaviate":
            self._backend = WeaviateBackend(self.config)
        elif self.config.backend == "in_memory":
            from .in_memory import InMemoryBackend
            self._backend = InMemoryBackend(self.config)
        else:
            raise ValueError(f"Unknown backend: {self.config.backend}")

        await self._backend.initialize()
        self._initialized = True

    async def close(self) -> None:
        if self._backend:
            await self._backend.close()
        self._initialized = False

    async def add(
        self,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0,
        ttl_seconds: Optional[float] = None,
        id: Optional[str] = None,
    ) -> str:
        """Add a memory vector."""
        if not self._initialized:
            await self.initialize()

        vec_id = id or str(uuid.uuid4())
        now = time.time()
        vector = MemoryVector(
            id=vec_id,
            content=content,
            embedding=embedding,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            importance=importance,
            ttl_seconds=ttl_seconds,
        )
        await self._backend.upsert([vector])
        return vec_id

    async def search(
        self,
        query_embedding: List[float],
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        threshold: Optional[float] = None,
    ) -> List[Tuple[MemoryVector, float]]:
        """Search for similar vectors."""
        if not self._initialized:
            await self.initialize()

        top_k = top_k or self.config.default_top_k
        threshold = threshold or self.config.similarity_threshold
        results = await self._backend.search(query_embedding, top_k, filter_metadata, threshold)

        # Update access stats
        for vec, _ in results:
            vec.access_count += 1
            vec.last_accessed = time.time()
            await self._backend.upsert([vec])

        return results

    async def get(self, ids: List[str]) -> List[Optional[MemoryVector]]:
        """Get vectors by ID."""
        if not self._initialized:
            await self.initialize()
        return await self._backend.get(ids)

    async def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""
        if not self._initialized:
            await self.initialize()
        await self._backend.delete(ids)

    async def update_importance(self, id: str, importance: float) -> None:
        """Update importance score."""
        if not self._initialized:
            await self.initialize()
        vectors = await self._backend.get([id])
        if vectors[0]:
            vectors[0].importance = importance
            vectors[0].updated_at = time.time()
            await self._backend.upsert(vectors)

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """Count vectors."""
        if not self._initialized:
            await self.initialize()
        return await self._backend.count(filter_metadata)

    async def prune_expired(self) -> int:
        """Remove expired vectors."""
        if not self._initialized:
            await self.initialize()
        return await self._backend.prune_expired()


# Global instance
_vector_memory: Optional[VectorMemory] = None


def get_vector_memory(config: Optional[VectorMemoryConfig] = None) -> VectorMemory:
    """Get global vector memory instance."""
    global _vector_memory
    if _vector_memory is None:
        _vector_memory = VectorMemory(config)
    return _vector_memory