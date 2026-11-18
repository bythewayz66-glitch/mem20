"""In-memory vector backend for testing and development.

Supports two modes:
- "flat": brute-force linear scan (exact, slow, no index build)
- "hnsw": HNSW index via hnswlib (fast, approximate, requires hnswlib)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import struct
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


class MemoryBackend(VectorBackend):
    """In-memory vector backend for testing.

    Not suitable for production use — no persistence, no concurrent write safety
    beyond basic locking, no disk spillover.
    """

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._mode = config.memory_backend  # "flat" or "hnsw"
        self._dimension = config.dimension
        self._records: dict[str, VectorRecord] = {}
        self._lock = threading.RLock()
        self._hnsw_index: Any = None
        self._id_to_label: dict[str, int] = {}
        self._label_to_id: list[str] = []
        self._build_time = 0.0

    @property
    def name(self) -> str:
        return "memory"

    @property
    def supports_filter(self) -> bool:
        return True

    @property
    def supports_filter_expr(self) -> bool:
        return False

    @property
    def supports_payload(self) -> bool:
        return True

    @property
    def supports_delete(self) -> bool:
        return True

    @property
    def supports_update(self) -> bool:
        return True

    @property
    def supports_persist(self) -> bool:
        return False

    @property
    def supports_replica(self) -> bool:
        return False

    @property
    def is_distributed(self) -> bool:
        return False

    @property
    def max_dimension(self) -> int:
        return 0  # unlimited

    async def initialize(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._mode = config.memory_backend

        if self._mode == "hnsw":
            await self._init_hnsw()
        else:
            self._build_time = 0.0

        logger.info("MemoryBackend initialized: mode=%s, dim=%d", self._mode, self._dimension)

    async def _init_hnsw(self) -> None:
        try:
            import hnswlib
        except ImportError:
            logger.warning("hnswlib not installed, falling back to flat mode")
            self._mode = "flat"
            return

        self._hnsw_index = hnswlib.Index(space="cosine", dim=self._dimension)
        self._hnsw_index.init_index(
            max_elements=100000,
            ef_construction=200,
            M=16,
        )
        self._hnsw_index.set_ef(50)
        self._id_to_label = {}
        self._label_to_id = []
        self._build_time = 0.0

    async def close(self) -> None:
        with self._lock:
            self._records.clear()
            self._hnsw_index = None
            self._id_to_label.clear()
            self._label_to_id.clear()

    async def add(self, records: list[VectorRecord]) -> None:
        with self._lock:
            vectors = []
            labels = []
            for record in records:
                if record.vector.shape[0] != self._dimension:
                    raise ValueError(
                        f"Vector dimension mismatch: expected {self._dimension}, got {record.vector.shape[0]}"
                    )
                self._records[record.id] = record

                if self._mode == "hnsw" and self._hnsw_index is not None:
                    if record.id not in self._id_to_label:
                        label = len(self._label_to_id)
                        self._id_to_label[record.id] = label
                        self._label_to_id.append(record.id)
                        vectors.append(record.vector)
                        labels.append(label)

            if vectors and self._hnsw_index is not None:
                import time
                start = time.perf_counter()
                self._hnsw_index.add_items(np.stack(vectors), np.array(labels))
                self._build_time += time.perf_counter() - start

    async def delete(self, ids: list[str]) -> None:
        with self._lock:
            for id_ in ids:
                self._records.pop(id_, None)
                # Note: HNSW doesn't support true delete; mark via filter or rebuild on compact

    async def update(self, records: list[VectorRecord]) -> None:
        with self._lock:
            for record in records:
                if record.id not in self._records:
                    raise KeyError(f"Cannot update non-existent ID: {record.id}")
                if record.vector.shape[0] != self._dimension:
                    raise ValueError("Dimension mismatch")
                self._records[record.id] = record

                if self._mode == "hnsw" and self._hnsw_index is not None:
                    if record.id in self._id_to_label:
                        label = self._id_to_label[record.id]
                        self._hnsw_index.add_items(record.vector.reshape(1, -1), np.array([label]))

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        with self._lock:
            if not self._records:
                return []

            qvec = query.vector
            k = min(query.k, len(self._records))

            # Apply metadata filter first
            candidates = self._filter_records(query.filter)

            if not candidates:
                return []

            if self._mode == "hnsw" and self._hnsw_index is not None and len(candidates) > 100:
                return await self._search_hnsw(qvec, k, candidates, query)
            else:
                return self._search_flat(qvec, k, candidates, query)

    def _filter_records(self, filter_: Optional[dict[str, Any]]) -> list[VectorRecord]:
        if not filter_:
            return list(self._records.values())

        result = []
        for record in self._records.values():
            match = True
            for key, value in filter_.items():
                if record.metadata.get(key) != value:
                    match = False
                    break
            if match:
                result.append(record)
        return result

    def _search_flat(
        self,
        qvec: np.ndarray,
        k: int,
        candidates: list[VectorRecord],
        query: SearchQuery,
    ) -> list[SearchResult]:
        # Brute-force cosine similarity
        qnorm = np.linalg.norm(qvec)
        if qnorm == 0:
            return []

        scores = []
        for record in candidates:
            vnorm = np.linalg.norm(record.vector)
            if vnorm == 0:
                continue
            score = float(np.dot(qvec, record.vector) / (qnorm * vnorm))
            scores.append((score, record))

        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for rank, (score, record) in enumerate(scores[:k]):
            r = record
            if not query.include_payload:
                r = VectorRecord(r.id, r.vector, r.metadata, {})
            if not query.include_vector:
                r = VectorRecord(r.id, np.array([], dtype=np.float32), r.metadata, r.payload)
            results.append(SearchResult(record=r, score=score, rank=rank))
        return results

    async def _search_hnsw(
        self,
        qvec: np.ndarray,
        k: int,
        candidates: list[VectorRecord],
        query: SearchQuery,
    ) -> list[SearchResult]:
        # Filter candidate labels
        candidate_labels = [
            self._id_to_label[r.id] for r in candidates if r.id in self._id_to_label
        ]
        if not candidate_labels:
            return []

        # HNSW doesn't support label filtering directly; search larger set then filter
        search_k = min(k * 10, len(self._label_to_id))
        labels, distances = self._hnsw_index.knn_query(qvec.reshape(1, -1), k=search_k)
        labels = labels[0]
        distances = distances[0]

        # Convert distance to cosine similarity (hnswlib cosine space: 1 - cos)
        results = []
        seen = set()
        for label, dist in zip(labels, distances):
            if label in seen:
                continue
            seen.add(label)
            if label >= len(self._label_to_id):
                continue
            record_id = self._label_to_id[label]
            record = self._records.get(record_id)
            if record is None:
                continue
            if query.filter and not self._matches_filter(record, query.filter):
                continue

            score = 1.0 - float(dist)
            r = record
            if not query.include_payload:
                r = VectorRecord(r.id, r.vector, r.metadata, {})
            if not query.include_vector:
                r = VectorRecord(r.id, np.array([], dtype=np.float32), r.metadata, r.payload)
            results.append(SearchResult(record=r, score=score, rank=len(results)))
            if len(results) >= k:
                break

        return results

    def _matches_filter(self, record: VectorRecord, filter_: dict[str, Any]) -> bool:
        for key, value in filter_.items():
            if record.metadata.get(key) != value:
                return False
        return True

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        with self._lock:
            return [self._records.get(id_) for id_ in ids]

    async def compact(self) -> None:
        with self._lock:
            if self._mode == "hnsw" and self._hnsw_index is not None:
                # Rebuild HNSW from current records
                await self._init_hnsw()
                if self._records:
                    records = list(self._records.values())
                    vectors = np.stack([r.vector for r in records])
                    labels = np.arange(len(records))
                    self._label_to_id = [r.id for r in records]
                    self._id_to_label = {r.id: i for i, r in enumerate(records)}
                    import time
                    start = time.perf_counter()
                    self._hnsw_index.add_items(vectors, labels)
                    self._build_time += time.perf_counter() - start

    async def stats(self) -> IndexStats:
        with self._lock:
            import sys
            size = sum(
                sys.getsizeof(r.vector) + sys.getsizeof(r.metadata) + sys.getsizeof(r.payload)
                for r in self._records.values()
            )
            return IndexStats(
                num_vectors=len(self._records),
                dimension=self._dimension,
                index_size_bytes=size,
                backend_name="memory",
                backend_version=self._mode,
                index_type=self._mode,
                build_time_seconds=self._build_time,
            )

    async def backup(self, path: str) -> None:
        # Not persistent, but export for migration
        with self._lock:
            out = Path(path)
            out.mkdir(parents=True, exist_ok=True)

            # Write vectors as binary
            vectors_file = out / "vectors.bin"
            meta_file = out / "metadata.json"

            with open(vectors_file, "wb") as vf:
                for record in self._records.values():
                    vf.write(struct.pack("I", len(record.id)))
                    vf.write(record.id.encode("utf-8"))
                    vf.write(struct.pack("I", record.vector.shape[0]))
                    vf.write(record.vector.tobytes())
                    meta_json = json.dumps({"metadata": record.metadata, "payload": record.payload}).encode("utf-8")
                    vf.write(struct.pack("I", len(meta_json)))
                    vf.write(meta_json)

    async def restore(self, path: str) -> None:
        with self._lock:
            self._records.clear()
            self._id_to_label.clear()
            self._label_to_id.clear()

            vectors_file = Path(path) / "vectors.bin"
            if not vectors_file.exists():
                return

            with open(vectors_file, "rb") as vf:
                while True:
                    id_len_bytes = vf.read(4)
                    if not id_len_bytes:
                        break
                    id_len = struct.unpack("I", id_len_bytes)[0]
                    id_ = vf.read(id_len).decode("utf-8")
                    dim = struct.unpack("I", vf.read(4))[0]
                    vec_bytes = vf.read(dim * 4)
                    vector = np.frombuffer(vec_bytes, dtype=np.float32)
                    meta_len = struct.unpack("I", vf.read(4))[0]
                    meta_json = vf.read(meta_len).decode("utf-8")
                    meta = json.loads(meta_json)

                    record = VectorRecord(
                        id=id_,
                        vector=vector,
                        metadata=meta.get("metadata", {}),
                        payload=meta.get("payload", {}),
                    )
                    self._records[id_] = record

            if self._mode == "hnsw":
                await self.compact()


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("memory", lambda config: MemoryBackend(config))


_register()