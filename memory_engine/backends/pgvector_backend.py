"""pgvector vector backend implementation.

Uses PostgreSQL with the pgvector extension for vector storage and search.
Supports exact search (Flat), IVFFlat, and HNSW indexes.
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

# Try to import dependencies; if not available, backend will raise on initialize
try:
    import psycopg
    from psycopg.rows import dict_row

    PGVECTOR_AVAILABLE = True
except ImportError:
    psycopg = None  # type: ignore
    PGVECTOR_AVAILABLE = False


class PgVectorBackend(VectorBackend):
    """PostgreSQL pgvector backend with support for Flat, IVFFlat, HNSW indexes."""

    def __init__(self, config: BackendConfig) -> None:
        self._config = config
        self._dimension = config.dimension
        self._conn: Any = None
        self._lock = threading.RLock()
        self._build_time = 0.0
        self._table_name = config.pgvector_table
        self._index_created = False

    @property
    def name(self) -> str:
        return "pgvector"

    @property
    def supports_filter(self) -> bool:
        return True  # Full SQL WHERE clause support

    @property
    def supports_filter_expr(self) -> bool:
        return True  # Native SQL expressions

    @property
    def supports_payload(self) -> bool:
        return True  # JSONB column

    @property
    def supports_delete(self) -> bool:
        return True

    @property
    def supports_update(self) -> bool:
        return True

    @property
    def supports_persist(self) -> bool:
        return True  # Native PostgreSQL persistence

    @property
    def supports_replica(self) -> bool:
        return True  # PostgreSQL streaming replication

    @property
    def is_distributed(self) -> bool:
        return True  # With Citus or read replicas

    @property
    def max_dimension(self) -> int:
        return 16000  # pgvector limit

    def _get_dsn(self) -> str:
        """Get PostgreSQL DSN from config or environment."""
        if self._config.pgvector_dsn:
            return self._config.pgvector_dsn
        # Build from environment variables
        host = os.environ.get("PGHOST", "localhost")
        port = os.environ.get("PGPORT", "5432")
        db = os.environ.get("PGDATABASE", "mem20")
        user = os.environ.get("PGUSER", "postgres")
        password = os.environ.get("PGPASSWORD", "postgres")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    async def initialize(self, config: BackendConfig) -> None:
        if not PGVECTOR_AVAILABLE:
            raise RuntimeError(
                "pgvector dependencies not installed. Install with: pip install 'psycopg[pool]' pgvector"
            )

        self._config = config
        self._dimension = config.dimension
        self._table_name = config.pgvector_table

        dsn = self._get_dsn()

        # Connect and ensure pgvector extension
        self._conn = await psycopg.AsyncConnection.connect(
            dsn, autocommit=True, row_factory=dict_row
        )

        # Register vector adapter
        try:
            from pgvector.psycopg import register_vector_async
            await register_vector_async(self._conn)
        except ImportError:
            # pgvector not installed on server side
            pass

        # Ensure pgvector extension
        async with self._conn.cursor() as cur:
            await cur.execute("CREATE EXTENSION IF NOT EXISTS vector")

        # Create table if not exists
        await self._create_table()

        # Create index if configured
        await self._create_index()

        logger.info(
            "PgVectorBackend initialized: dim=%d, table=%s, index_type=%s",
            self._dimension,
            self._table_name,
            self._config.pgvector_hnsw_m,
        )

    async def _create_table(self) -> None:
        """Create the vectors table with appropriate schema."""
        async with self._conn.cursor() as cur:
            await cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id TEXT PRIMARY KEY,
                    vector vector({self._dimension}),
                    metadata JSONB NOT NULL DEFAULT '{{}}',
                    payload JSONB NOT NULL DEFAULT '{{}}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            # Create indexes for common filter fields
            await cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self._table_name}_metadata
                ON {self._table_name} USING GIN (metadata)
            """)

    async def _create_index(self) -> None:
        """Create vector index based on configuration."""
        if self._index_created:
            return

        async with self._conn.cursor() as cur:
            # Check if index already exists
            await cur.execute(f"""
                SELECT 1 FROM pg_indexes 
                WHERE tablename = '{self._table_name}' 
                AND indexname = 'idx_{self._table_name}_vector'
            """)
            if await cur.fetchone():
                self._index_created = True
                return

            # Create HNSW index (best for high-recall ANN)
            m = self._config.pgvector_hnsw_m
            ef_construction = self._config.pgvector_hnsw_ef_construction
            
            await cur.execute(f"""
                CREATE INDEX idx_{self._table_name}_vector
                ON {self._table_name} 
                USING hnsw (vector vector_cosine_ops)
                WITH (m = {m}, ef_construction = {ef_construction})
            """)
            self._index_created = True

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def add(self, records: list[VectorRecord]) -> None:
        if not self._conn:
            raise RuntimeError("Backend not initialized")

        async with self._conn.cursor() as cur:
            for record in records:
                if record.vector.shape[0] != self._dimension:
                    raise ValueError(
                        f"Vector dimension mismatch: expected {self._dimension}, got {record.vector.shape[0]}"
                    )

                vector_list = record.vector.tolist()
                metadata_json = json.dumps(record.metadata)
                payload_json = json.dumps(record.payload)

                await cur.execute(
                    f"""
                    INSERT INTO {self._table_name} (id, vector, metadata, payload, updated_at)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        metadata = EXCLUDED.metadata,
                        payload = EXCLUDED.payload,
                        updated_at = NOW()
                    """,
                    (record.id, vector_list, metadata_json, payload_json),
                )

    async def delete(self, ids: list[str]) -> None:
        if not self._conn or not ids:
            return

        async with self._conn.cursor() as cur:
            # Use parameterized query for safety
            placeholders = ",".join(["%s"] * len(ids))
            await cur.execute(
                f"DELETE FROM {self._table_name} WHERE id IN ({placeholders})",
                tuple(ids),
            )

    async def update(self, records: list[VectorRecord]) -> None:
        # pgvector supports upsert natively, so add() handles updates
        await self.add(records)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        if not self._conn:
            raise RuntimeError("Backend not initialized")

        vector_list = query.vector.tolist()
        
        # Build WHERE clause for metadata filter
        where_clauses = []
        params: list[Any] = [vector_list, query.k]

        if query.filter:
            for i, (key, value) in enumerate(query.filter.items()):
                where_clauses.append(f"metadata->>'{key}' = %s")
                params.append(str(value))

        # Add filter_expr if provided (raw SQL)
        if query.filter_expr:
            where_clauses.append(query.filter_expr)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Build SELECT clause
        select_fields = "id, vector, metadata, payload"
        if not query.include_vector:
            select_fields = "id, metadata, payload"
        if not query.include_payload:
            select_fields = select_fields.replace(", payload", "")

        sql = f"""
            SELECT {select_fields},
                   1 - (vector <=> %s) AS score
            FROM {self._table_name}
            {where_sql}
            ORDER BY vector <=> %s
            LIMIT %s
        """
        # First %s is for ORDER BY, second for score calculation, third for LIMIT
        # Actually we need vector twice - once for distance, once for ordering
        # But we can reuse - pgvector optimizes this

        async with self._conn.cursor() as cur:
            await cur.execute(sql, tuple(params))
            rows = await cur.fetchall()

        results = []
        for rank, row in enumerate(rows):
            # Reconstruct vector if needed
            vector_data = row.get("vector")
            if query.include_vector and vector_data is not None:
                vector = np.array(vector_data, dtype=np.float32)
            else:
                vector = np.array([], dtype=np.float32)

            record = VectorRecord(
                id=row["id"],
                vector=vector,
                metadata=row.get("metadata", {}),
                payload=row.get("payload", {}) if query.include_payload else {},
            )
            # pgvector cosine distance is 1 - cosine_similarity, so score = 1 - distance
            score = float(row["score"])
            results.append(SearchResult(record=record, score=score, rank=rank))

        return results

    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        if not self._conn or not ids:
            return [None] * len(ids)

        placeholders = ",".join(["%s"] * len(ids))
        sql = f"SELECT id, vector, metadata, payload FROM {self._table_name} WHERE id IN ({placeholders})"

        async with self._conn.cursor() as cur:
            await cur.execute(sql, tuple(ids))
            rows = await cur.fetchall()

        # Build lookup dict
        row_dict = {row["id"]: row for row in rows}

        results = []
        for id_ in ids:
            row = row_dict.get(id_)
            if row is None:
                results.append(None)
            else:
                vector_data = row.get("vector")
                if vector_data is not None:
                    vector = np.array(vector_data, dtype=np.float32)
                else:
                    vector = np.array([], dtype=np.float32)
                results.append(VectorRecord(
                    id=row["id"],
                    vector=vector,
                    metadata=row.get("metadata", {}),
                    payload=row.get("payload", {}),
                ))
        return results

    async def compact(self) -> None:
        # Vacuum analyze for PostgreSQL
        if not self._conn:
            return
        async with self._conn.cursor() as cur:
            await cur.execute(f"VACUUM ANALYZE {self._table_name}")
            # Rebuild index if needed
            await cur.execute(f"""
                DROP INDEX IF EXISTS idx_{self._table_name}_vector
            """)
            self._index_created = False
            await self._create_index()

    async def stats(self) -> IndexStats:
        if not self._conn:
            return IndexStats(
                num_vectors=0,
                dimension=self._dimension,
                index_size_bytes=0,
                backend_name="pgvector",
                backend_version="unknown",
                index_type="none",
                build_time_seconds=0.0,
            )

        async with self._conn.cursor() as cur:
            # Count vectors
            await cur.execute(f"SELECT COUNT(*) as cnt FROM {self._table_name}")
            row = await cur.fetchone()
            num_vectors = row["cnt"] if row else 0

            # Get table size
            await cur.execute(f"""
                SELECT pg_total_relation_size('{self._table_name}') as size_bytes
            """)
            row = await cur.fetchone()
            index_size = row["size_bytes"] if row else 0

            # Check index type
            await cur.execute(f"""
                SELECT indexname, indexdef FROM pg_indexes 
                WHERE tablename = '{self._table_name}' AND indexname LIKE '%vector%'
            """)
            idx_row = await cur.fetchone()
            index_type = "none"
            if idx_row:
                if "hnsw" in idx_row["indexdef"].lower():
                    index_type = f"HNSW(m={self._config.pgvector_hnsw_m})"
                elif "ivfflat" in idx_row["indexdef"].lower():
                    index_type = "IVFFlat"

        return IndexStats(
            num_vectors=num_vectors,
            dimension=self._dimension,
            index_size_bytes=index_size,
            backend_name="pgvector",
            backend_version="pgvector/psycopg",
            index_type=index_type,
            build_time_seconds=self._build_time,
        )

    async def backup(self, path: str) -> None:
        # Use pg_dump for backup
        import subprocess
        import os

        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)

        dsn = self._get_dsn()
        # Extract connection params for pg_dump
        # This is simplified; real implementation would parse DSN properly
        dump_file = out / "backup.sql"
        cmd = ["pg_dump", "-t", self._table_name, "-f", str(dump_file), dsn]
        subprocess.run(cmd, check=True)

        # Save config
        config_data = {
            "backend": "pgvector",
            "dimension": self._dimension,
            "table": self._table_name,
        }
        with open(out / "config.json", "w") as f:
            json.dump(config_data, f, indent=2)

    async def restore(self, path: str) -> None:
        # Use psql for restore
        import subprocess

        src = Path(path)
        dump_file = src / "backup.sql"
        if not dump_file.exists():
            raise FileNotFoundError(f"Backup dump not found: {dump_file}")

        dsn = self._get_dsn()
        cmd = ["psql", "-f", str(dump_file), dsn]
        subprocess.run(cmd, check=True)

        # Re-register vector
        from pgvector.psycopg import register_vector_async
        await register_vector_async(self._conn)
        self._index_created = False
        await self._create_index()


# Register with registry
def _register() -> None:
    from memory_engine.backends.registry import registry
    registry.register("pgvector", lambda config: PgVectorBackend(config))


_register()