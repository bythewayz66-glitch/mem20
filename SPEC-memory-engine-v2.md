# SPEC: Unified Memory Engine v2 — Pluggable Vector Backends

**Status:** Draft  
**Author:** glyph-cluster  
**Created:** 2026-11-17  
**Target:** mem20 4.1 / 5.0  
**Related:** #1 from improvement brainstorm

---

## 1. Problem Statement

The current `memory_engine` package (in `/opt/mem20/memory_engine`) hardcodes FAISS as the sole vector backend. This creates:

- **Vendor lock-in** — users cannot swap to pgvector, Qdrant, Milvus, LanceDB, Weaviate, or future backends
- **Operational rigidity** — no cloud-managed option (e.g., Pinecone, Weaviate Cloud, Qdrant Cloud)
- **Scaling limits** — FAISS is single-node; distributed workloads require manual sharding
- **Feature gaps** — no hybrid search (vector + keyword), no metadata filtering at index level, no tenant isolation
- **Testing burden** — all tests require FAISS + GPU for parity; no fast in-memory backend for CI

---

## 2. Goals

| Goal | Success Metric |
|------|----------------|
| **Pluggable backend interface** | Add/swap backend in ≤50 lines of user code |
| **Zero-breaking migration** | Existing FAISS users upgrade with config change only |
| **Backend parity** | All backends pass same conformance suite (≥95% feature coverage) |
| **Performance** | ≤10% overhead vs. raw FAISS for single-node workloads |
| **Observability** | Per-backend metrics: latency p50/p99, index size, build time, recall@k |
| **Testing** | Fast in-memory backend (`memory://`) runs full test suite in <30s CI |

---

## 3. Non-Goals (v2)

- SQL/relational backend (handled by separate `memory_sql` package)
- Graph backend (handled by `mem20graphz`)
- Multi-model embedding routing (handled by `mem20routerz`)
- Automatic backend selection (v3: cost/performance optimizer)

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MemoryEngine (public API)                │
│  store(), recall(), search(), delete(), compact(), stats()  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  BackendRegistry (singleton)                │
│  register(name, factory), get(name), list(), default        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ FAISS    │   │ pgvector │   │ Qdrant   │
        │ Backend  │   │ Backend  │   │ Backend  │
        └──────────┘   └──────────┘   └──────────┘
              ▲               ▲               ▲
              │               │               │
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ LanceDB  │   │ Milvus   │   │ Weaviate │
        │ Backend  │   │ Backend  │   │ Backend  │
        └──────────┘   └──────────┘   └──────────┘
              ▲               ▲               ▲
              └───────────────┼───────────────┘
                              ▼
                    ┌──────────────────┐
                    │  VectorBackend   │  (ABC / Protocol)
                    │  (interface)     │
                    └──────────────────┘
```

---

## 5. Interface Specification

### 5.1 Core Protocol (`memory_engine/backends/base.py`)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal, Optional
import numpy as np

@dataclass(frozen=True, slots=True)
class VectorRecord:
    """A single vector with metadata and optional payload."""
    id: str                    # unique, user-provided or UUID
    vector: np.ndarray         # shape (dim,), dtype float32
    metadata: dict[str, Any]   # filterable fields (tenant, tags, timestamps)
    payload: dict[str, Any]    # opaque, returned on recall (text, blobs)

@dataclass(frozen=True, slots=True)
class SearchQuery:
    vector: np.ndarray
    k: int = 10
    filter: Optional[dict[str, Any]] = None      # exact match on metadata
    filter_expr: Optional[str] = None            # backend-specific expr (SQL, Lucene, etc.)
    include_payload: bool = True
    include_vector: bool = False

@dataclass(frozen=True, slots=True)
class SearchResult:
    record: VectorRecord
    score: float                  # cosine similarity [0,1] or distance
    rank: int                     # 0-based

@dataclass(frozen=True, slots=True)
class IndexStats:
    num_vectors: int
    dimension: int
    index_size_bytes: int
    backend_name: str
    backend_version: str
    index_type: str               # "HNSW", "IVF", "DiskANN", etc.
    build_time_seconds: float

class VectorBackend(ABC):
    """Abstract base class for all vector backends."""

    # ─── Capability flags (static, no I/O) ───
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def supports_filter(self) -> bool: ...
    @property
    @abstractmethod
    def supports_filter_expr(self) -> bool: ...
    @property
    @abstractmethod
    def supports_payload(self) -> bool: ...
    @property
    @abstractmethod
    def supports_delete(self) -> bool: ...
    @property
    @abstractmethod
    def supports_update(self) -> bool: ...
    @property
    @abstractmethod
    def supports_persist(self) -> bool: ...
    @property
    @abstractmethod
    def supports_replica(self) -> bool: ...
    @property
    @abstractmethod
    def is_distributed(self) -> bool: ...
    @property
    @abstractmethod
    def max_dimension(self) -> int: ...

    # ─── Lifecycle ───
    @abstractmethod
    async def initialize(self, config: BackendConfig) -> None:
        """Create index, connect to service, validate schema."""
    @abstractmethod
    async def close(self) -> None:
        """Flush, release connections, cleanup temp files."""

    # ─── Write path ───
    @abstractmethod
    async def add(self, records: list[VectorRecord]) -> None:
        """Batch insert. Must be idempotent on id conflict (upsert)."""
    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Soft delete by default; hard delete if backend supports."""
    @abstractmethod
    async def update(self, records: list[VectorRecord]) -> None:
        """Optional: full record replacement. Default: delete + add."""

    # ─── Read path ───
    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Top-k ANN search with optional filtering."""
    @abstractmethod
    async def get(self, ids: list[str]) -> list[Optional[VectorRecord]]:
        """Exact lookup by id. Returns None for missing."""

    # ─── Maintenance ───
    @abstractmethod
    async def compact(self) -> None:
        """Merge segments, reclaim deleted space, rebuild index."""
    @abstractmethod
    async def stats(self) -> IndexStats:
        """Current index statistics."""
    @abstractmethod
    async def backup(self, path: str) -> None:
        """Export index + metadata to portable format."""
    @abstractmethod
    async def restore(self, path: str) -> None:
        """Import from backup. Replaces current index."""
```

### 5.2 Configuration (`memory_engine/backends/config.py`)

```python
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

@dataclass(frozen=True, slots=True)
class BackendConfig:
    backend: Literal["faiss", "pgvector", "qdrant", "lancedb", "milvus", "weaviate", "memory"]
    dimension: int

    # FAISS-specific
    faiss_index_type: str = "HNSW32"          # "Flat", "IVF1024,Flat", "HNSW32", "DiskANN"
    faiss_metric: str = "cosine"              # "cosine", "l2", "ip"
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
    lancedb_index_type: str = "IVF_PQ"        # "IVF_PQ", "IVF_FLAT", "HNSW"

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
    weaviate_vectorizer: str = "none"         # "none", "text2vec-openai", etc.

    # Memory (in-memory, for testing)
    memory_backend: Literal["flat", "hnsw"] = "flat"

    # Common
    batch_size: int = 1024
    num_threads: int = 0                      # 0 = auto
    cache_size_gb: float = 0.0                # 0 = no cache

    # Extensibility
    extra: dict[str, Any] = field(default_factory=dict)
```

### 5.3 Public API (`memory_engine/__init__.py`)

```python
from memory_engine.engine import MemoryEngine
from memory_engine.backends.config import BackendConfig

__all__ = ["MemoryEngine", "BackendConfig"]
```

```python
# memory_engine/engine.py
class MemoryEngine:
    def __init__(self, config: BackendConfig):
        self._backend = BackendRegistry.get(config.backend)(config)
        self._config = config

    async def __aenter__(self):
        await self._backend.initialize(self._config)
        return self

    async def __aexit__(self, *args):
        await self._backend.close()

    # High-level API (unchanged from v1)
    async def store(self, texts: list[str], embeddings: list[np.ndarray], metadatas: list[dict]) -> list[str]:
        ...
    async def recall(self, query_embedding: np.ndarray, k: int = 10, filter: dict = None) -> list[RecallResult]:
        ...
    async def search(self, query: str, k: int = 10, filter: dict = None) -> list[SearchResult]:
        ...
    async def delete(self, ids: list[str]) -> None:
        ...
    async def compact(self) -> None:
        ...
    async def stats(self) -> EngineStats:
        ...
```

---

## 6. Backend Implementation Matrix

| Feature | FAISS | pgvector | Qdrant | LanceDB | Milvus | Weaviate | Memory |
|---------|-------|----------|--------|---------|--------|----------|--------|
| **Vector search** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Metadata filter** | ❌ | ✅ (SQL) | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Filter expression** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Payload storage** | ❌ | ✅ (JSONB) | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Delete** | ⚠️ rebuild | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Update** | ⚠️ rebuild | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Persist** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Replication** | ❌ | ✅ (PG) | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Distributed** | ❌ | ✅ (Citus) | ✅ | ❌ | ✅ | ✅ | ❌ |
| **Hybrid search** | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Tenant isolation** | ❌ | ✅ (RLS) | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Cloud managed** | ❌ | ✅ (RDS) | ✅ | ❌ | ✅ (Zilliz) | ✅ (WCS) | ❌ |
| **License** | MIT | PostgreSQL | Apache-2.0 | Apache-2.0 | LGPL/SLP | BSD-3 | MIT |

---

## 7. Migration Path (Zero-Breaking)

### 7.1 Current v1 User Code (Unchanged)

```python
from memory_engine import MemoryEngine, BackendConfig

config = BackendConfig(
    backend="faiss",
    dimension=768,
    faiss_index_type="HNSW32",
)
async with MemoryEngine(config) as engine:
    await engine.store(texts, embeddings, metadatas)
```

### 7.2 New Backend — Config Only

```python
config = BackendConfig(
    backend="qdrant",
    dimension=768,
    qdrant_url="http://localhost:6333",
    qdrant_collection="my_vectors",
)
```

### 7.3 Advanced: Multi-Backend (Future)

```python
from memory_engine import MultiBackendEngine

engine = MultiBackendEngine(
    primary=BackendConfig(backend="faiss", ...),
    replicas=[
        BackendConfig(backend="qdrant", qdrant_url="...", ...),
        BackendConfig(backend="pgvector", pgvector_dsn="...", ...),
    ],
    read_preference="replica",  # or "primary", "nearest"
)
```

---

## 8. Conformance Test Suite (`tests/backends/conformance.py`)

Every backend **must** pass:

```python
import pytest
from memory_engine.backends.base import VectorBackend, VectorRecord, SearchQuery

class TestBackendConformance:
    @pytest.fixture
    def backend(self, backend_name: str) -> VectorBackend:
        return BackendRegistry.get(backend_name)(default_config(backend_name))

    @pytest.mark.asyncio
    async def test_add_and_search(self, backend: VectorBackend):
        records = [VectorRecord(id=f"vec-{i}", vector=rand_vec(768), metadata={"tag": "test"}, payload={}) for i in range(1000)]
        await backend.add(records)
        results = await backend.search(SearchQuery(vector=rand_vec(768), k=10))
        assert len(results) == 10
        assert all(0 <= r.score <= 1 for r in results)

    @pytest.mark.asyncio
    async def test_filter_exact_match(self, backend: VectorBackend):
        if not backend.supports_filter:
            pytest.skip("backend does not support filter")
        # ...

    @pytest.mark.asyncio
    async def test_delete(self, backend: VectorBackend):
        if not backend.supports_delete:
            pytest.skip("backend does not support delete")
        # ...

    @pytest.mark.asyncio
    async def test_persist_restore(self, backend: VectorBackend, tmp_path):
        if not backend.supports_persist:
            pytest.skip("backend does not support persist")
        # ...

    @pytest.mark.asyncio
    async def test_recall_at_k(self, backend: VectorBackend):
        # Ground truth: brute-force cosine on 10k vectors
        # Require recall@10 ≥ 0.95 for HNSW backends
        ...

    @pytest.mark.asyncio
    async def test_latency_p99(self, backend: VectorBackend):
        # Warm up, then 1000 queries, p99 < 50ms for 1M vectors (HNSW)
        ...

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, backend: VectorBackend):
        # 10 concurrent writers, 10k vectors each, no data loss
        ...
```

**Run:** `pytest tests/backends/conformance.py -v --backend=faiss,pgvector,qdrant,lancedb,milvus,weaviate,memory`

---

## 9. Phased Implementation Plan

### Phase 0: Foundation (Week 1-2) — **CRITICAL PATH**

| Task | Owner | Deliverable |
|------|-------|-------------|
| Define `VectorBackend` ABC + `VectorRecord`, `SearchQuery`, `SearchResult`, `IndexStats` | Core team | `memory_engine/backends/base.py` |
| Implement `BackendRegistry` (entry-point + explicit register) | Core team | `memory_engine/backends/registry.py` |
| Extract FAISS logic into `FaissBackend` implementing ABC | Core team | `memory_engine/backends/faiss_backend.py` |
| Wire `MemoryEngine` to use registry + backend | Core team | Updated `memory_engine/engine.py` |
| Write conformance test skeleton | Core team | `tests/backends/conformance.py` |
| CI: Run conformance on FAISS + Memory backends | DevOps | Green CI |

**Exit criteria:** All existing tests pass; `backend="memory"` runs full suite in <30s.

---

### Phase 1: Core Backends (Week 3-6) — **COMPLETED**

| Backend | Effort | Dependencies | Priority | Status |
|---------|--------|--------------|----------|--------|
| **pgvector** | 1 week | `psycopg[pool]`, `pgvector` Python | 🔴 Critical | ✅ Done |
| **Qdrant** | 1 week | `qdrant-client` | 🔴 Critical | ✅ Done |
| **LanceDB** | 1 week | `lancedb` | 🟡 High | ✅ Done |
| **Milvus** | 1.5 weeks | `pymilvus` | 🟡 High | ✅ Done |
| **Weaviate** | 1.5 weeks | `weaviate-client` | 🟢 Medium | ✅ Done |

**Per-backend checklist:**
- [x] Implement `VectorBackend` subclass
- [x] Add to `BackendRegistry` entry points (`pyproject.toml`)
- [x] Document config options in `BackendConfig`
- [x] All 7 backends constructible and registered

**Implementation files:**
- `memory_engine/backends/pgvector_backend.py` — PostgreSQL + pgvector with HNSW/IVF indexes
- `memory_engine/backends/qdrant_backend.py` — Qdrant with payload filtering, hybrid search
- `memory_engine/backends/lancedb_backend.py` — LanceDB embedded columnar with IVF_PQ/HNSW
- `memory_engine/backends/milvus_backend.py` — Milvus distributed with HNSW/IVF/DiskANN
- `memory_engine/backends/weaviate_backend.py` — Weaviate with GraphQL, modular vectorizers

**Updated `pyproject.toml`:**
- Added optional dependencies: `faiss`, `pgvector`, `qdrant`, `lancedb`, `milvus`, `weaviate`, `all-backends`
- Registered all 7 backends as entry points in `mem20.vector_backends` group
- [ ] Add integration test (real service in CI via Testcontainers)
- [ ] Benchmark: 1M vectors, 768-dim, HNSW, recall@10, latency p50/p99

---

### Phase 2: Advanced Features (Week 7-10)

| Feature | Description | Backends |
|---------|-------------|----------|
| **Hybrid search** | Vector + BM25/keyword in single query | pgvector, Qdrant, Milvus, Weaviate |
| **Filter expressions** | Backend-native filter DSL (SQL, Lucene, etc.) | All except FAISS, Memory |
| **Tenant isolation** | Row-level security / collection per tenant | pgvector (RLS), Qdrant, Milvus, Weaviate |
| **Replication / read replicas** | Async replica sync, read preference | pgvector, Qdrant, Milvus, Weaviate |
| **Backup/restore** | Portable format (Parquet + metadata JSON) | All persistent backends |
| **Quantization** | PQ/SQ/INT8 on build, auto-select | FAISS, Qdrant, Milvus, LanceDB |

---

### Phase 3: Production Hardening (Week 11-14)

| Task | Description |
|------|-------------|
| **Soak tests** | 72h continuous write/read/delete, 10M vectors, check for leaks |
| **Chaos tests** | Kill backend mid-write, network partition, disk full, OOM |
| **Migration tool** | `mem20 migrate --from faiss --to qdrant --verify` |
| **Benchmark CI** | Nightly Bencher runs, alert on >5% regression |
| **Documentation** | Backend comparison guide, tuning guide, troubleshooting |
| **Examples** | `examples/backend_comparison.py`, `examples/hybrid_search.py` |

---

### Phase 4: v3 Features (Post-v2)

- **Cost/performance optimizer** — auto-select backend per workload
- **Tiered storage** — hot (HNSW RAM) → warm (DiskANN SSD) → cold (object store)
- **Multi-model routing** — different backends per embedding model
- **Federated search** — single query across multiple backends/clusters

---

## 10. Resource Estimates

| Phase | Engineering Weeks | Infra Cost (CI/nightly) | Risk |
|-------|-------------------|-------------------------|------|
| 0: Foundation | 2 | Low (existing) | Low |
| 1: 5 Backends | 6 | Medium (Testcontainers) | Medium (API churn) |
| 2: Advanced | 4 | Medium | Medium |
| 3: Hardening | 4 | High (soak/chaos) | Low |
| **Total** | **~16 weeks** | **~$2-5k/mo** | **Medium** |

**Team:** 2 engineers (1 core, 1 backend specialist) + 0.5 DevOps

---

## 11. Success Criteria (v2 Release)

| Metric | Target |
|--------|--------|
| **Conformance pass rate** | 100% for FAISS, pgvector, Qdrant, LanceDB, Memory; ≥90% for Milvus, Weaviate |
| **Latency overhead** | ≤10% vs. raw client for single-node |
| **Recall@10** | ≥0.95 on 1M vectors (HNSW backends) |
| **CI time** | Full conformance suite < 10 min |
| **Migration** | Zero code changes for FAISS → any backend |
| **Documentation** | Every backend has: quickstart, config ref, tuning guide, known limitations |

---

## 12. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backend API instability (pre-1.0) | High | Medium | Pin versions; integration tests in CI; abstraction layer absorbs breaking changes |
| Feature parity impossible (e.g., FAISS no filter) | Certain | High | Document capability matrix; `supports_*` flags; graceful degradation |
| Performance regression on FAISS | Medium | High | Benchmark CI; `faiss_backend` is reference implementation |
| License issues (Milvus SSPL, Weaviate BSD) | Low | High | Legal review; optional dependencies; user opts in |
| Distributed backend complexity | High | High | Phase 1: single-node only; Phase 2: replication; Phase 4: federation |

---

## 13. Appendix: File Tree (Target)

```
memory_engine/
├── __init__.py
├── engine.py
├── backends/
│   ├── __init__.py
│   ├── base.py              # VectorBackend ABC + dataclasses
│   ├── config.py            # BackendConfig
│   ├── registry.py          # BackendRegistry + entry points
│   ├── faiss_backend.py
│   ├── pgvector_backend.py
│   ├── qdrant_backend.py
│   ├── lancedb_backend.py
│   ├── milvus_backend.py
│   ├── weaviate_backend.py
│   └── memory_backend.py    # In-memory for testing
├── tests/
│   ├── test_engine.py
│   └── backends/
│       ├── conformance.py   # Parametrized across backends
│       ├── test_faiss.py
│       ├── test_pgvector.py
│       ├── test_qdrant.py
│       ├── test_lancedb.py
│       ├── test_milvus.py
│       ├── test_weaviate.py
│       └── test_memory.py
└── examples/
    ├── backend_comparison.py
    ├── hybrid_search.py
    └── migration_faiss_to_qdrant.py
```

---

## 14. Next Steps

1. **Approve this spec** — review with team, resolve open questions
2. **Create GitHub milestone** — "Memory Engine v2: Pluggable Backends"
3. **File issues** — one per backend + foundation tasks
4. **Assign owners** — Phase 0 starts immediately
5. **Weekly sync** — Friday 15:00 UTC, track progress against plan

---

*End of SPEC*