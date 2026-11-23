"""Weaviate vector backend implementation.

Uses Weaviate vector database for vector storage and search.
Supports HNSW indexes, GraphQL API, and modular vectorizers.
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
    import weaviate
    from weaviate.classes.config import Property, DataType, Configure
    from weaviate.classes.query import Filter, MetadataQuery

    WEAVIATE_AVAILABLE = True
except ImportError:
    weaviate = None  # type: ignore
    WEAVIATE_AVAILABLE = False


class WeaviateBackend(VectorBackend):
    """Weaviate vector backend with HNSW index and GraphQL-style filtering."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._client: Any = None
        self._collection: Any = None
        self._lock = threading.RLock()
        self._build_time = 0.0
        self._url = config.weaviate_url
        self._api_key = config.weaviate_api_key
        self._class_name = config.weaviate_class
        self._vectorizer = config.weaviate_vectorizer

    @property
    def name(self) -> str:
        return "weaviate"

    @property
    def supports_filter(self) -> bool:
        return True  # Full GraphQL/Weaviate filter

    @property
    def supports_filter_expr(self) -> bool:
        return True  # Weaviate filter DSL

    @property
    def supports_payload(self) -> bool:
        return True  # Native properties

    @property
    def supports_delete(self) -> bool:
        return True

    @property
    def supports_update(self) -> bool:
        return True

    @property
    def supports_persist(self) -> bool:
        return True

    @property
    def supports_replica(self) -> bool:
        return True  # Weaviate replicas

    @property
    def is_distributed(self) -> bool:
        return True  # Native distributed

    @property
    def max_dimension(self) -> int:
        return 0  # No hard limit

    def _get_url(self) -> str:
        if self._config.weaviate_url:
            return self._config.weaviate_url
        return os.environ.get("WEAVIATE_URL", "http://localhost:8080")

    def _get_api_key(self) -> Optional[str]:
        if self._config.weaviate_api_key:
            return self._config.weaviate_api_key
        return os.environ.get("WEAVIATE_API_KEY")

    async def initialize(self, config: BackendConfig) -> None:
        if not WEAVIATE_AVAILABLE:
            raise RuntimeError(
                "Weaviate client not installed. Install with: pip install weaviate-client"
            )

        self._config = config
        self._dimension = config.dimension
        self._url = config.weaviate_url
        self._api_key = config.weaviate_api_key
        self._class_name = config.weaviate_class
        self._vectorizer = config.weaviate_vectorizer

        url = self._get_url()
        api_key = self._get_api_key()

        # Connect to Weaviate
        if api_key:
            self._client = weaviate.connect_to_weaviate_cloud(
                cluster_url=url,
                auth_credentials=weaviate.auth.AuthApiKey(api_key),
            )
        else:
            # Parse host:port from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8080
            grpc_port = port + 1 if port == 8080 else 50051
            
            self._client = weaviate.connect_to_local(
                host=host,
                port=port,
                grpc_port=grpc_port,
            )

        # Ensure collection exists
        await self._ensure_collection()

        self._collection = self._client.collections.get(self._class_name)

        logger.info(
            "WeaviateBackend initialized: dim=%d, class=%s, url=%s",
            self._dimension,
            self._class_name,
            url,
        )

    async def _ensure_collection(self) -> None:
        """Create collection with schema if it doesn't exist."""
        if self._client.collections.exists(self._class_name):
            logger.info("Collection %s already exists", self._class_name)
            return

        # Create collection with vectorizer="none" (we provide vectors)
        self._client.collections.create(
            name=self._class_name,
            properties=[
                Property(name="id", data_type=DataType.TEXT),
                Property(name="metadata", data_type=DataType.OBJECT),
                Property(name="payload", data_type=DataType.OBJECT),
            ],
            vectorizer_config=Configure.Vectorizer.none(),
            vector_index_config=Configure.VectorIndex.hnsw(
                distance_metric="cosine",
                quantizer=Configure.VectorIndex.Quantizer.pq(),
            ),
        )
        logger.info("Created Weaviate collection: %s", self._class_name)

    async def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None
            self._collection = None

    async def add(self, records: list[VectorRecord]) -> None:
        if not self._collection:
            raise RuntimeError("Backend not initialized")

        with self._collection.batch.dynamic() as batch:
            for record in records:
                if record.vector.shape[0] != self._dimension:
                    raise ValueError(
                        f"Vector dimension mismatch: expected {self._dimension}, got {record.vector.shape[0]}"
                    )

                batch.add_object(
                    properties={
                        "id": record.id,
                        "metadata": record.metadata,
                        "payload": record.payload,
                    },
                    vector=record.vector.tolist(),
                    uuid=record.id,  # Use id as UUID if valid, otherwise let Weaviate generate
                )

    async def delete(self, ids: list[str]) -> None:
        if not self._collection or not ids:
            return

        # Delete by ID filter
        from weaviate.classes.query import Filter
        id_filter = Filter.by_property("id").contains_any(ids)
        self._collection.data.delete_many(where=id_filter)

    async def update(self, records: list[VectorRecord]) -> None:
        # Weaviate: delete + insert (or use batch update)
        await self.delete([r.id for r in records])
        await self.add(records)

    def _build_weaviate_filter(self, filter_dict: dict[str, Any]) -> Any:
        """Convert simple dict filter to Weaviate Filter."""
        from weaviate.classes.query import Filter
        
        filters = []
        for key, value in filter_dict.items():
            filters.append(Filter.by_property("metadata").by_key(key).equal(value))
        
        if not filters:
            return None
        
        # Combine with AND
        result = filters[0]
        for f in filters[1:]:
            result = result & f
        return result

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        if not self._collection:
            raise RuntimeError("Backend not initialized")

        # Build filter
        where_filter = None
        if query.filter:
            where_filter = self._build_weaviate_filter(query.filter)

        # Build return properties
        return_props = ["id", "metadata", "payload"]
        if not query.include_payload:
            return_props = ["id", "metadata"]

        # Execute vector search
        results = self._collection.query.near_vector(
            near_vector=query.vector.tolist(),
            limit=query.k,
            where=where_filter,
            return_properties=return_props,
            return_metadata=MetadataQuery(distance=True, certainty=True),
        )

        search_results = []
        for rank, hit in enumerate(results.objects):
            properties = hit.properties or {}
            
            metadata = properties.get("metadata", {})
            payload = properties.get("payload", {})

            vector = np.array([], dtype=np.float32)
            if query.include_vector and hit.vector:
                vector = np.array(hit.vector["default"], dtype=np.float32)

            record = VectorRecord(
                id=properties.get("id", str(hit.uuid)),
                vector=vector,
                metadata=metadata,
                payload=payload if query.include_payload else {},
            )

            # Weaviate returns certainty (cosine similarity) and distance
            metadata_obj = hit.metadata
            if metadata_obj and metadata_obj.certainty is not None:
                score = float(metadata_obj.certainty)
            elif metadata_obj and metadata_obj.distance is not None:
                score = max(0.0, 1.0 - float(metadata_obj.distance))
            else:
                score = 0.0

            search_results.append(SearchResult(record=record, score=score, rank=rank))

        return search_results

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        if not self._collection or not ids:
            return [None] * len(ids)

        from weaviate.classes.query import Filter
        id_filter = Filter.by_property("id").contains_any(ids)

        results = self._collection.query.fetch_objects(
            where=id_filter,
            return_properties=["id", "metadata", "payload"],
            return_metadata=MetadataQuery(),
        )

        hit_dict = {}
        for hit in results.objects:
            props = hit.properties or {}
            hit_dict[props.get("id", str(hit.uuid))] = hit

        records = []
        for id_ in ids:
            hit = hit_dict.get(id_)
            if hit is None:
                records.append(None)
            else:
                props = hit.properties or {}
                metadata = props.get("metadata", {})
                payload = props.get("payload", {})
                records.append(VectorRecord(
                    id=id_,
                    vector=np.array([], dtype=np.float32),
                    metadata=metadata,
                    payload=payload,
                ))
        return records

    async def compact(self) -> None:
        # Weaviate handles compaction automatically
        pass

    async def stats(self) -> IndexStats:
        if not self._collection:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="weaviate",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

        try:
            # Get collection count
            agg = self._collection.aggregate.over_all(total_count=True)
            count = agg.total_count if agg else 0

            return IndexStats(
                num_vectors=count,
                dimension=self._dimension,
                index_size_bytes=0,  # Weaviate doesn't expose directly
                backend_name="weaviate",
                backend_version="weaviate-client",
                index_type="HNSW(PQ)",
                build_time_seconds=self._build_time,
            )
        except Exception:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="weaviate",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

    async def backup(self, path: str) -> None:
        # Weaviate backup via API
        import json
        from pathlib import Path

        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)

        config_data = {
            "backend": "weaviate",
            "dimension": self._dimension,
            "class": self._class_name,
            "vectorizer": self._vectorizer,
        }
        with open(out / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)

    async def restore(self, path: str) -> None:
        # Weaviate restore via API
        src = Path(path)
        if not src.exists():
            raise FileNotFoundError(f"Backup path not found: {path}")


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("weaviate", lambda config: WeaviateBackend(config))


_register()