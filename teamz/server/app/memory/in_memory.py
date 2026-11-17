"""In-memory vector backend for testing and development."""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .vector import VectorBackend, MemoryVector, VectorMemoryConfig


@dataclass
class InMemoryVectorEntry:
    """An entry in the in-memory vector store."""
    vector: MemoryVector
    embedding: List[float]


class InMemoryBackend(VectorBackend):
    """In-memory vector storage backend for testing."""

    def __init__(self, config: VectorMemoryConfig) -> None:
        self.config = config
        self._vectors: Dict[str, InMemoryVectorEntry] = {}

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def initialize(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def upsert(self, vectors: List[MemoryVector]) -> None:
        for vec in vectors:
            self._vectors[vec.id] = InMemoryVectorEntry(
                vector=vec,
                embedding=vec.embedding,
            )

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None,
        threshold: float = 0.0,
    ) -> List[Tuple[MemoryVector, float]]:
        results = []

        for entry in self._vectors.values():
            vec = entry.vector

            # Check filter
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if key not in vec.metadata or vec.metadata[key] != value:
                        match = False
                        break
                if not match:
                    continue

            # Compute similarity
            similarity = self._cosine_similarity(query_embedding, entry.embedding)
            if similarity >= threshold:
                results.append((vec, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    async def delete(self, ids: List[str]) -> None:
        for id_ in ids:
            self._vectors.pop(id_, None)

    async def get(self, ids: List[str]) -> List[Optional[MemoryVector]]:
        results = []
        for id_ in ids:
            entry = self._vectors.get(id_)
            if entry:
                results.append(entry.vector)
            else:
                results.append(None)
        return results

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        if not filter_metadata:
            return len(self._vectors)

        count = 0
        for entry in self._vectors.values():
            match = True
            for key, value in filter_metadata.items():
                if key not in entry.vector.metadata or entry.vector.metadata[key] != value:
                    match = False
                    break
            if match:
                count += 1
        return count

    async def prune_expired(self) -> int:
        now = time.time()
        expired = [
            id_ for id_, entry in self._vectors.items()
            if entry.vector.ttl_seconds is not None
            and entry.vector.created_at + entry.vector.ttl_seconds < now
        ]
        for id_ in expired:
            del self._vectors[id_]
        return len(expired)