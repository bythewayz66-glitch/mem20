"""FAISS vector backend implementation.

Wraps the existing FAISS index logic from memory_engine.memory into the
VectorBackend interface.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
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

# Try to import faiss; if not available, backend will raise on initialize
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    faiss = None  # type: ignore
    FAISS_AVAILABLE = False


class FaissBackend(VectorBackend):
    """FAISS vector backend with support for Flat, IVF, HNSW index types."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._index: Any = None
        self._meta: list[dict[str, Any]] = []
        self._meta_path: Optional[Path] = None
        self._index_path: Optional[Path] = None
        self._lock = threading.RLock()
        self._build_time = 0.0
        self._store_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "faiss"

    @property
    def supports_filter(self) -> bool:
        # FAISS itself doesn't support filtering; we do post-filtering on metadata
        return True

    @property
    def supports_filter_expr(self) -> bool:
        return False

    @property
    def supports_payload(self) -> bool:
        return False  # Payload stored separately in ledger

    @property
    def supports_delete(self) -> bool:
        return True  # Via rebuild (soft delete not supported natively)

    @property
    def supports_update(self) -> bool:
        return True  # Via rebuild

    @property
    def supports_persist(self) -> bool:
        return True

    @property
    def supports_replica(self) -> bool:
        return False

    @property
    def is_distributed(self) -> bool:
        return False

    @property
    def max_dimension(self) -> int:
        return 0  # No hard limit

    async def initialize(self, config: BackendConfig) -> None:
        if not FAISS_AVAILABLE:
            raise RuntimeError("FAISS not installed. Install with: pip install faiss-cpu")

        self._config = config
        self._dimension = config.dimension

        # Determine store path
        store_path = os.environ.get("MEM20_STORE_PATH", "~/.mem20/store")
        self._store_path = Path(store_path).expanduser().resolve()
        self._store_path.mkdir(parents=True, exist_ok=True)

        self._index_path = self._store_path / "vector_index.faiss"
        self._meta_path = self._store_path / "vector_meta.json"
        self._vectors_path = self._store_path / "vector_vectors.npy"

        # Load or create index
        await self._load_or_create_index()

        logger.info(
            "FaissBackend initialized: dim=%d, index_type=%s, ntotal=%d",
            self._dimension,
            self._config.faiss_index_type,
            self._index.ntotal if self._index else 0,
        )

    async def _load_or_create_index(self) -> None:
        import time

        start = time.perf_counter()

        if self._index_path.exists() and self._meta_path.exists() and self._vectors_path.exists():
            # Load existing index
            self._index = faiss.read_index(str(self._index_path))
            with open(self._meta_path, "r") as f:
                self._meta = json.load(f)
            self._vectors = np.load(self._vectors_path)
        else:
            # Create new index
            self._index = self._create_index()
            self._meta = []
            self._vectors = np.empty((0, self._dimension), dtype=np.float32)

        self._build_time = time.perf_counter() - start

    def _create_index(self) -> Any:
        """Create a new FAISS index based on config."""
        index_type = self._config.faiss_index_type.upper()

        if index_type == "FLAT":
            # Flat index (exact search)
            if self._config.faiss_metric == "cosine":
                return faiss.IndexFlatIP(self._dimension)
            elif self._config.faiss_metric == "l2":
                return faiss.IndexFlatL2(self._dimension)
            else:
                return faiss.IndexFlatIP(self._dimension)

        elif index_type.startswith("IVF"):
            # IVF index (inverted file)
            # Format: "IVF1024,Flat" or "IVF1024,PQ16"
            parts = index_type.split(",", 1)
            nlist = int(parts[0][3:])  # IVF1024 -> 1024
            quantizer_type = parts[1] if len(parts) > 1 else "Flat"

            if self._config.faiss_metric == "cosine":
                quantizer = faiss.IndexFlatIP(self._dimension)
            else:
                quantizer = faiss.IndexFlatL2(self._dimension)

            if quantizer_type == "Flat":
                index = faiss.IndexIVFFlat(quantizer, self._dimension, nlist, faiss.METRIC_INNER_PRODUCT)
            elif quantizer_type.startswith("PQ"):
                m = int(quantizer_type[2:])  # PQ16 -> 16
                index = faiss.IndexIVFPQ(quantizer, self._dimension, nlist, m, 8)
            else:
                raise ValueError(f"Unknown IVF quantizer: {quantizer_type}")

            return index

        elif index_type.startswith("HNSW"):
            # HNSW index (hierarchical navigable small world)
            # Format: "HNSW32" -> M=32
            # Use inner product (cosine) metric with normalized vectors
            m = int(index_type[4:]) if len(index_type) > 4 else 32
            index = faiss.IndexHNSWFlat(self._dimension, m, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efConstruction = self._config.faiss_ef_construction
            index.hnsw.efSearch = self._config.faiss_ef_search
            return index

        else:
            # Default to HNSW32
            index = faiss.IndexHNSWFlat(self._dimension, 32)
            index.hnsw.efConstruction = 128
            index.hnsw.efSearch = 64
            return index

    def _normalize(self, vectors: np.ndarray) -> np.ndarray:
        """Normalize vectors for cosine similarity."""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vectors / norms

    async def close(self) -> None:
        with self._lock:
            await self._save()
            self._index = None
            self._meta = []

    async def _save(self) -> None:
        if self._index is not None and self._index_path is not None:
            import time
            start = time.perf_counter()
            faiss.write_index(self._index, str(self._index_path))
            with open(self._meta_path, "w") as f:
                json.dump(self._meta, f)
            if hasattr(self, "_vectors") and self._vectors is not None:
                np.save(self._vectors_path, self._vectors)
            self._build_time += time.perf_counter() - start

    async def add(self, records: list[VectorRecord]) -> None:
        with self._lock:
            if self._index is None:
                raise RuntimeError("Backend not initialized")

            vectors = []
            meta_entries = []

            for record in records:
                if record.vector.shape[0] != self._dimension:
                    raise ValueError(
                        f"Vector dimension mismatch: expected {self._dimension}, got {record.vector.shape[0]}"
                    )

                # Normalize for cosine similarity
                vec = self._normalize(record.vector.reshape(1, -1)).astype(np.float32)
                vectors.append(vec)

                meta_entry = {
                    "id": record.id,
                    "metadata": record.metadata,
                    "payload": record.payload,
                }
                meta_entries.append(meta_entry)

            if vectors:
                new_vectors = np.vstack(vectors)
                # Train IVF index if needed
                if hasattr(self._index, "is_trained") and not self._index.is_trained:
                    train_data = new_vectors
                    if train_data.shape[0] < 100:
                        # Need more data to train; use existing vectors if available
                        if hasattr(self, "_vectors") and self._vectors.shape[0] > 0:
                            train_data = np.vstack([self._vectors, new_vectors])
                    self._index.train(train_data)

                self._index.add(new_vectors)
                self._meta.extend(meta_entries)
                # Store vectors for rebuild capability
                if hasattr(self, "_vectors") and self._vectors.shape[0] > 0:
                    self._vectors = np.vstack([self._vectors, new_vectors])
                else:
                    self._vectors = new_vectors

            await self._save()

    async def _rebuild_index(self) -> None:
        """Rebuild FAISS index from stored vectors and metadata."""
        import time
        start = time.perf_counter()

        if not hasattr(self, "_vectors") or self._vectors.shape[0] == 0:
            # Nothing to rebuild
            self._index = self._create_index()
        else:
            # Rebuild index from all stored vectors
            self._index = self._create_index()
            if hasattr(self._index, "is_trained") and not self._index.is_trained:
                self._index.train(self._vectors)
            self._index.add(self._vectors)

        self._build_time += time.perf_counter() - start

    async def delete(self, ids: list[str]) -> None:
        with self._lock:
            # FAISS doesn't support native delete; rebuild index
            id_set = set(ids)
            # Find indices of vectors to remove
            keep_indices = [i for i, m in enumerate(self._meta) if m["id"] not in id_set]
            self._meta = [m for m in self._meta if m["id"] not in id_set]
            # Also remove corresponding vectors
            if hasattr(self, "_vectors") and self._vectors.shape[0] > 0:
                self._vectors = self._vectors[keep_indices]
            await self._rebuild_index()
            await self._save()

    async def update(self, records: list[VectorRecord]) -> None:
        with self._lock:
            # FAISS doesn't support native update; delete + add + rebuild
            ids = [r.id for r in records]
            # Find indices of vectors to remove
            keep_indices = [i for i, m in enumerate(self._meta) if m["id"] not in ids]
            self._meta = [m for m in self._meta if m["id"] not in ids]
            # Also remove corresponding vectors
            if hasattr(self, "_vectors") and self._vectors.shape[0] > 0:
                self._vectors = self._vectors[keep_indices]
            # Rebuild index with remaining vectors
            await self._rebuild_index()
            # Add new/updated records
            await self.add(records)
            # Note: add() calls _save(), so we don't need to call it again

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        with self._lock:
            if self._index is None or self._index.ntotal == 0:
                return []

            # Normalize query vector
            qvec = self._normalize(query.vector.reshape(1, -1)).astype(np.float32)

            # Set search parameters for IVF/HNSW
            if hasattr(self._index, "nprobe"):
                self._index.nprobe = self._config.faiss_nprobe
            if hasattr(self._index, "hnsw"):
                self._index.hnsw.efSearch = self._config.faiss_ef_search

            # Oversample for filtering
            search_k = min(max(query.k * 10, 50), self._index.ntotal)
            scores, indices = self._index.search(qvec, search_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1 or idx >= len(self._meta):
                    continue

                meta = self._meta[idx]

                # Apply metadata filter
                if query.filter:
                    match = True
                    for key, value in query.filter.items():
                        if meta.get("metadata", {}).get(key) != value:
                            match = False
                            break
                    if not match:
                        continue

                # Build result record
                record = VectorRecord(
                    id=meta["id"],
                    vector=np.array([], dtype=np.float32) if not query.include_vector else np.zeros(self._dimension, dtype=np.float32),
                    metadata=meta.get("metadata", {}),
                    payload=meta.get("payload", {}) if query.include_payload else {},
                )

                # FAISS returns inner product for IndexFlatIP (cosine similarity)
                # Score is already cosine similarity [-1, 1], convert to [0, 1]
                normalized_score = (float(score) + 1.0) / 2.0
                normalized_score = max(0.0, min(1.0, normalized_score))

                results.append(SearchResult(record=record, score=normalized_score, rank=len(results)))

                if len(results) >= query.k:
                    break

            return results

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        with self._lock:
            id_to_meta = {m["id"]: m for m in self._meta}
            results = []
            for id_ in ids:
                meta = id_to_meta.get(id_)
                if meta is None:
                    results.append(None)
                else:
                    results.append(VectorRecord(
                        id=meta["id"],
                        vector=np.array([], dtype=np.float32),  # Vectors not stored in meta
                        metadata=meta.get("metadata", {}),
                        payload=meta.get("payload", {}),
                    ))
            return results

    async def compact(self) -> None:
        with self._lock:
            if self._index is None:
                return

            # Rebuild index from current metadata
            import time
            start = time.perf_counter()

            if not self._meta:
                # Empty index
                self._index = self._create_index()
            else:
                # We don't have vectors stored, so we can't truly rebuild
                # In a real implementation, vectors would be stored or we'd
                # re-embed from the ledger. For now, just recreate.
                self._index = self._create_index()

            self._build_time += time.perf_counter() - start
            await self._save()

    async def stats(self) -> IndexStats:
        with self._lock:
            import sys
            index_size = 0
            if self._index_path and self._index_path.exists():
                index_size = self._index_path.stat().st_size
            if self._meta_path and self._meta_path.exists():
                index_size += self._meta_path.stat().st_size

            return IndexStats(
                num_vectors=self._index.ntotal if self._index else 0,
                dimension=self._dimension,
                index_size_bytes=index_size,
                backend_name="faiss",
                backend_version=getattr(faiss, "__version__", "unknown"),
                index_type=self._config.faiss_index_type,
                build_time_seconds=self._build_time,
            )

    async def backup(self, path: str) -> None:
        with self._lock:
            out = Path(path)
            out.mkdir(parents=True, exist_ok=True)

            # Copy index and meta files
            if self._index_path and self._index_path.exists():
                import shutil
                shutil.copy2(self._index_path, out / "vector_index.faiss")
            if self._meta_path and self._meta_path.exists():
                import shutil
                shutil.copy2(self._meta_path, out / "vector_meta.json")

            # Write config
            config_data = {
                "backend": "faiss",
                "dimension": self._dimension,
                "faiss_index_type": self._config.faiss_index_type,
                "faiss_metric": self._config.faiss_metric,
            }
            with open(out / "config.json", "w") as f:
                json.dump(config_data, f, indent=2)

    async def restore(self, path: str) -> None:
        with self._lock:
            src = Path(path)
            if not src.exists():
                raise FileNotFoundError(f"Backup path not found: {path}")

            # Load config
            config_file = src / "config.json"
            if config_file.exists():
                with open(config_file) as f:
                    config_data = json.load(f)
                self._config.faiss_index_type = config_data.get("faiss_index_type", self._config.faiss_index_type)

            # Load index and meta
            index_file = src / "vector_index.faiss"
            meta_file = src / "vector_meta.json"

            if index_file.exists():
                self._index = faiss.read_index(str(index_file))
            else:
                self._index = self._create_index()

            if meta_file.exists():
                with open(meta_file) as f:
                    self._meta = json.load(f)
            else:
                self._meta = []

            await self._save()


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("faiss", lambda config: FaissBackend(config))


_register()