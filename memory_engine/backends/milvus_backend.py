"""Milvus vector backend implementation.

Uses Milvus distributed vector database for vector storage and search.
Supports HNSW, IVF, DiskANN indexes with horizontal scaling.
"""

from __future__ import annotations

import json
import logging
import os
import threading
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
    from pymilvus import (
        MilvusClient,
        DataType,
        Function,
        FunctionType,
    )

    MILVUS_AVAILABLE = True
except ImportError:
    MilvusClient = None  # type: ignore
    DataType = None  # type: ignore
    MILVUS_AVAILABLE = False


class MilvusBackend(VectorBackend):
    """Milvus vector backend with HNSW, IVF, DiskANN indexes."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._client: Optional[MilvusClient] = None
        self._lock = threading.RLock()
        self._build_time = 0.0
        self._uri = config.milvus_uri
        self._token = config.milvus_token
        self._collection_name = config.milvus_collection
        self._index_type = config.milvus_index_type
        self._metric_type = config.milvus_metric_type

    @property
    def name(self) -> str:
        return "milvus"

    @property
    def supports_filter(self) -> bool:
        return True  # Full boolean expression filtering

    @property
    def supports_filter_expr(self) -> bool:
        return True  # Milvus filter expressions

    @property
    def supports_payload(self) -> bool:
        return True  # Dynamic fields / JSON

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
        return True  # Milvus replicas

    @property
    def is_distributed(self) -> bool:
        return True  # Native distributed

    @property
    def max_dimension(self) -> int:
        return 32768  # Milvus limit

    def _get_uri(self) -> str:
        if self._config.milvus_uri:
            return self._config.milvus_uri
        return os.environ.get("MILVUS_URI", "http://localhost:19530")

    def _get_token(self) -> Optional[str]:
        if self._config.milvus_token:
            return self._config.milvus_token
        return os.environ.get("MILVUS_TOKEN")

    async def initialize(self, config: BackendConfig) -> None:
        if not MILVUS_AVAILABLE:
            raise RuntimeError(
                "Milvus client not installed. Install with: pip install pymilvus"
            )

        self._config = config
        self._dimension = config.dimension
        self._uri = config.milvus_uri
        self._token = config.milvus_token
        self._collection_name = config.milvus_collection
        self._index_type = config.milvus_index_type
        self._metric_type = config.milvus_metric_type

        uri = self._get_uri()
        token = self._get_token()

        self._client = MilvusClient(uri=uri, token=token)

        # Create collection if not exists
        await self._ensure_collection()

        # Create index if needed
        await self._ensure_index()

        logger.info(
            "MilvusBackend initialized: dim=%d, collection=%s, uri=%s, index=%s",
            self._dimension,
            self._collection_name,
            uri,
            self._index_type,
        )

    async def _ensure_collection(self) -> None:
        """Create collection with schema if it doesn't exist."""
        if self._client.has_collection(self._collection_name):
            logger.info("Collection %s already exists", self._collection_name)
            return

        # Define schema
        schema = self._client.create_schema(
            auto_id=False,
            enable_dynamic_field=True,  # For flexible metadata/payload
        )

        schema.add_field("id", DataType.VARCHAR, max_length=256, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self._dimension)
        schema.add_field("metadata", DataType.JSON)
        schema.add_field("payload", DataType.JSON)

        # Prepare index parameters
        index_params = self._client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type=self._index_type,
            metric_type=self._metric_type,
            params=self._get_index_params(),
        )

        self._client.create_collection(
            collection_name=self._collection_name,
            schema=schema,
            index_params=index_params,
        )
        logger.info("Created Milvus collection: %s", self._collection_name)

    def _get_index_params(self) -> dict[str, Any]:
        """Get index parameters based on index type."""
        if self._index_type == "HNSW":
            return {"M": 16, "efConstruction": 200}
        elif self._index_type == "IVF_FLAT":
            return {"nlist": 1024}
        elif self._index_type == "IVF_SQ8":
            return {"nlist": 1024}
        elif self._index_type == "IVF_PQ":
            return {"nlist": 1024, "m": 16}
        elif self._index_type == "DISKANN":
            return {"search_list": 100}
        else:
            # Default HNSW
            return {"M": 16, "efConstruction": 200}

    async def _ensure_index(self) -> None:
        """Ensure index is built (Milvus creates it on collection creation with index_params)."""
        # Index is created with collection in Milvus 2.4+
        # We can check index status and wait if needed
        pass

    async def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    async def add(self, records: list[VectorRecord]) -> None:
        if not self._client:
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
                "metadata": record.metadata,
                "payload": record.payload,
            })

        # Upsert (insert or update)
        self._client.upsert(
            collection_name=self._collection_name,
            data=data,
        )

    async def delete(self, ids: list[str]) -> None:
        if not self._client or not ids:
            return

        self._client.delete(
            collection_name=self._collection_name,
            ids=ids,
        )

    async def update(self, records: list[VectorRecord]) -> None:
        # upsert handles updates
        await self.add(records)

    def _build_milvus_filter(self, filter_dict: dict[str, Any]) -> str:
        """Convert simple dict filter to Milvus boolean expression."""
        conditions = []
        for key, value in filter_dict.items():
            if isinstance(value, str):
                conditions.append(f'metadata["{key}"] == "{value}"')
            else:
                conditions.append(f'metadata["{key}"] == {value}')
        return " && ".join(conditions)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        if not self._client:
            raise RuntimeError("Backend not initialized")

        # Build filter expression
        filter_expr = None
        if query.filter:
            filter_expr = self._build_milvus_filter(query.filter)
        if query.filter_expr:
            # Combine with user-provided expression
            if filter_expr:
                filter_expr = f"({filter_expr}) && ({query.filter_expr})"
            else:
                filter_expr = query.filter_expr

        # Search parameters
        search_params = {"metric_type": self._metric_type}
        if self._index_type == "HNSW":
            search_params["params"] = {"ef": 128}
        elif self._index_type.startswith("IVF"):
            search_params["params"] = {"nprobe": 16}
        elif self._index_type == "DISKANN":
            search_params["params"] = {"search_list": 100}

        # Determine output fields
        output_fields = ["id", "metadata", "payload"]
        if query.include_vector:
            output_fields.append("vector")

        results = self._client.search(
            collection_name=self._collection_name,
            data=[query.vector.tolist()],
            limit=query.k,
            filter=filter_expr,
            output_fields=output_fields,
            search_params=search_params,
        )

        search_results = []
        hits = results[0] if results else []
        for rank, hit in enumerate(hits):
            entity = hit.get("entity", {})
            
            metadata = entity.get("metadata", {})
            payload = entity.get("payload", {})

            vector = np.array([], dtype=np.float32)
            if query.include_vector:
                vector = np.array(entity.get("vector", []), dtype=np.float32)

            record = VectorRecord(
                id=hit["id"],
                vector=vector,
                metadata=metadata,
                payload=payload if query.include_payload else {},
            )

            # Milvus returns distance for COSINE; convert to similarity
            distance = hit.get("distance", 0.0)
            if self._metric_type == "COSINE":
                score = max(0.0, 1.0 - float(distance))
            else:
                # For L2/IP, normalize differently
                score = 1.0 / (1.0 + float(distance))

            search_results.append(SearchResult(record=record, score=score, rank=rank))

        return search_results

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        if not self._client or not ids:
            return [None] * len(ids)

        # Build filter for IDs
        id_conditions = " || ".join([f'id == "{id_}"' for id_ in ids])
        
        results = self._client.query(
            collection_name=self._collection_name,
            filter=id_conditions,
            output_fields=["id", "vector", "metadata", "payload"],
        )

        hit_dict = {hit["id"]: hit for hit in results}

        records = []
        for id_ in ids:
            hit = hit_dict.get(id_)
            if hit is None:
                records.append(None)
            else:
                metadata = hit.get("metadata", {})
                payload = hit.get("payload", {})
                vector = np.array([], dtype=np.float32)
                if "vector" in hit:
                    vector = np.array(hit["vector"], dtype=np.float32)
                records.append(VectorRecord(
                    id=id_,
                    vector=vector,
                    metadata=metadata,
                    payload=payload,
                ))
        return records

    async def compact(self) -> None:
        if not self._client:
            return

        # Milvus: trigger compaction/flush
        try:
            self._client.flush(self._collection_name)
            # Compact segments
            self._client.compact(self._collection_name)
        except Exception as e:
            logger.warning("Milvus compact failed: %s", e)

    async def stats(self) -> IndexStats:
        if not self._client:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="milvus",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

        try:
            stats = self._client.get_collection_stats(self._collection_name)
            return IndexStats(
                num_vectors=stats.get("row_count", 0),
                dimension=self._dimension,
                index_size_bytes=0,  # Milvus doesn't expose directly
                backend_name="milvus",
                backend_version="pymilvus",
                index_type=self._index_type,
                build_time_seconds=self._build_time,
            )
        except Exception:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="milvus",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

    async def backup(self, path: str) -> None:
        # Milvus backup requires separate backup tool
        # This is a placeholder
        import json
        from pathlib import Path

        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)

        config_data = {
            "backend": "milvus",
            "dimension": self._dimension,
            "collection": self._collection_name,
            "index_type": self._index_type,
            "metric_type": self._metric_type,
        }
        with open(out / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)

    async def restore(self, path: str) -> None:
        # Milvus restore requires separate restore tool
        # This is a placeholder
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"Backup path not found: {path}")


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("milvus", lambda config: MilvusBackend(config))


_register()