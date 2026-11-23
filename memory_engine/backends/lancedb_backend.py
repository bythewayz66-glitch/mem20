"""LanceDB vector backend implementation.

Uses LanceDB embedded columnar store for vector storage and search.
Supports IVF_PQ, IVF_FLAT, HNSW indexes with automatic persistence.
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
    import lancedb

    LANCEDB_AVAILABLE = True
except ImportError:
    lancedb = None  # type: ignore
    LANCEDB_AVAILABLE = False


class LanceDBBackend(VectorBackend):
    """LanceDB vector backend with IVF_PQ, IVF_FLAT, HNSW indexes."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._db: Any = None
        self._table: Any = None
        self._lock = threading.RLock()
        self._build_time = 0.0
        self._uri = config.lancedb_uri
        self._table_name = config.lancedb_table
        self._index_type = config.lancedb_index_type

    @property
    def name(self) -> str:
        return "lancedb"

    @property
    def supports_filter(self) -> bool:
        return True  # Full SQL-like filtering

    @property
    def supports_filter_expr(self) -> bool:
        return True  # LanceDB filter expressions

    @property
    def supports_payload(self) -> bool:
        return True  # Native columnar storage

    @property
    def supports_delete(self) -> bool:
        return True

    @property
    def supports_update(self) -> bool:
        return True  # Merge/upsert supported

    @property
    def supports_persist(self) -> bool:
        return True  # Native persistence to disk

    @property
    def supports_replica(self) -> bool:
        return False  # Single-node embedded

    @property
    def is_distributed(self) -> bool:
        return False  # Embedded only

    @property
    def max_dimension(self) -> int:
        return 0  # No hard limit

    def _expand_uri(self) -> str:
        """Expand tilde in URI path."""
        uri = self._uri
        if uri.startswith("~"):
            uri = os.path.expanduser(uri)
        return uri

    async def initialize(self, config: BackendConfig) -> None:
        if not LANCEDB_AVAILABLE:
            raise RuntimeError(
                "LanceDB not installed. Install with: pip install lancedb"
            )

        self._config = config
        self._dimension = config.dimension
        self._uri = config.lancedb_uri
        self._table_name = config.lancedb_table
        self._index_type = config.lancedb_index_type

        uri = self._expand_uri()
        self._db = lancedb.connect(uri)

        # Create or open table
        try:
            self._table = self._db.open_table(self._table_name)
            logger.info("Opened existing LanceDB table: %s", self._table_name)
        except Exception:
            # Table doesn't exist, create it with schema
            import pyarrow as pa
            
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), self._dimension)),
                pa.field("metadata", pa.string()),  # JSON string
                pa.field("payload", pa.string()),   # JSON string
            ])
            
            self._table = self._db.create_table(self._table_name, schema=schema)
            logger.info("Created new LanceDB table: %s", self._table_name)

        # Create index if table has data
        await self._ensure_index()

        logger.info(
            "LanceDBBackend initialized: dim=%d, table=%s, uri=%s, index_type=%s",
            self._dimension,
            self._table_name,
            uri,
            self._index_type,
        )

    async def _ensure_index(self) -> None:
        """Create vector index based on configuration."""
        try:
            # Check if index exists
            if hasattr(self._table, 'list_indices'):
                indices = self._table.list_indices()
                if any('vector' in str(idx) for idx in indices):
                    return

            # Count rows to determine if we should create index
            count = self._table.count_rows()
            if count < 10:
                return  # Too few rows for index

            # Create index based on type
            if self._index_type == "IVF_PQ":
                self._table.create_index(
                    column="vector",
                    index_type="IVF_PQ",
                    metric="cosine",
                    num_partitions=256,
                    num_sub_vectors=96,
                )
            elif self._index_type == "IVF_FLAT":
                self._table.create_index(
                    column="vector",
                    index_type="IVF_FLAT",
                    metric="cosine",
                    num_partitions=256,
                )
            elif self._index_type == "HNSW":
                self._table.create_index(
                    column="vector",
                    index_type="HNSW",
                    metric="cosine",
                    m=16,
                    ef_construction=200,
                )
            else:
                # Default to IVF_PQ
                self._table.create_index(
                    column="vector",
                    index_type="IVF_PQ",
                    metric="cosine",
                    num_partitions=256,
                    num_sub_vectors=96,
                )
            logger.info("Created %s index on LanceDB table", self._index_type)
        except Exception as e:
            logger.warning("Failed to create LanceDB index: %s", e)

    async def close(self) -> None:
        # LanceDB doesn't require explicit close
        self._db = None
        self._table = None

    async def add(self, records: list[VectorRecord]) -> None:
        if not self._table:
            raise RuntimeError("Backend not initialized")

        data = []
        for record in records:
            if record.vector.shape[0] != self._dimension:
                raise ValueError(
                    f"Vector dimension mismatch: expected {self._dimension}, got {record.vector.shape[0]}"
                )

            data.append({
                "id": record.id,
                "vector": record.vector.tolist(),
                "metadata": json.dumps(record.metadata),
                "payload": json.dumps(record.payload),
            })

        # Upsert (merge on id)
        self._table.merge_insert("id").when_matched_update_all().when_not_matched_insert_all().execute(data)

    async def delete(self, ids: list[str]) -> None:
        if not self._table or not ids:
            return

        # LanceDB uses SQL-like delete
        id_list = "','".join(ids)
        self._table.delete(f"id IN ('{id_list}')")

    async def update(self, records: list[VectorRecord]) -> None:
        # merge_insert handles updates
        await self.add(records)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        if not self._table:
            raise RuntimeError("Backend not initialized")

        # Build filter
        where_clause = None
        if query.filter:
            conditions = []
            for key, value in query.filter.items():
                # Filter on metadata JSON
                conditions.append(f"json_extract(metadata, '$.{key}') = '{value}'")
            where_clause = " AND ".join(conditions)

        # Build query
        search_query = self._table.search(query.vector.tolist()).limit(query.k)

        if where_clause:
            search_query = search_query.where(where_clause, prefilter=True)

        if query.include_vector:
            search_query = search_query.select(["id", "vector", "metadata", "payload"])
        else:
            search_query = search_query.select(["id", "metadata", "payload"])

        # Execute search
        results = search_query.to_list()

        search_results = []
        for rank, hit in enumerate(results):
            # Parse JSON fields
            metadata = json.loads(hit.get("metadata", "{}"))
            payload = json.loads(hit.get("payload", "{}"))

            vector = np.array([], dtype=np.float32)
            if query.include_vector and "vector" in hit:
                vector = np.array(hit["vector"], dtype=np.float32)

            record = VectorRecord(
                id=hit["id"],
                vector=vector,
                metadata=metadata,
                payload=payload if query.include_payload else {},
            )

            # LanceDB returns distance; convert to similarity score
            # For cosine, distance = 1 - similarity
            distance = hit.get("_distance", 0.0)
            score = max(0.0, 1.0 - float(distance))

            search_results.append(SearchResult(record=record, score=score, rank=rank))

        return search_results

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        if not self._table or not ids:
            return [None] * len(ids)

        id_list = "','".join(ids)
        results = self._table.search().where(f"id IN ('{id_list}')").limit(len(ids)).to_list()

        hit_dict = {hit["id"]: hit for hit in results}

        records = []
        for id_ in ids:
            hit = hit_dict.get(id_)
            if hit is None:
                records.append(None)
            else:
                metadata = json.loads(hit.get("metadata", "{}"))
                payload = json.loads(hit.get("payload", "{}"))
                records.append(VectorRecord(
                    id=id_,
                    vector=np.array([], dtype=np.float32),
                    metadata=metadata,
                    payload=payload,
                ))
        return records

    async def compact(self) -> None:
        if not self._table:
            return

        # LanceDB: optimize by running compaction
        try:
            self._table.optimize()
            # Recreate index after compaction
            await self._ensure_index()
        except Exception as e:
            logger.warning("LanceDB compact failed: %s", e)

    async def stats(self) -> IndexStats:
        if not self._table:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="lancedb",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

        try:
            count = self._table.count_rows()
            # Get table size on disk (approximate)
            import os
            table_path = Path(self._expand_uri()) / self._table_name
            index_size = 0
            if table_path.exists():
                for f in table_path.rglob("*"):
                    if f.is_file():
                        index_size += f.stat().st_size

            return IndexStats(
                num_vectors=count,
                dimension=self._dimension,
                index_size_bytes=index_size,
                backend_name="lancedb",
                backend_version="lancedb",
                index_type=self._index_type,
                build_time_seconds=self._build_time,
            )
        except Exception:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="lancedb",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

    async def backup(self, path: str) -> None:
        # LanceDB tables are just files; copy the directory
        import shutil

        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)

        src = Path(self._expand_uri()) / self._table_name
        if src.exists():
            shutil.copytree(src, out / self._table_name, dirs_exist_ok=True)

        config_data = {
            "backend": "lancedb",
            "dimension": self._dimension,
            "table": self._table_name,
            "index_type": self._index_type,
        }
        with open(out / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)

    async def restore(self, path: str) -> None:
        import shutil

        src = Path(path) / self._table_name
        dst = Path(self._expand_uri()) / self._table_name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

        # Reconnect
        await self.initialize(self._config)


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("lancedb", lambda config: LanceDBBackend(config))


_register()