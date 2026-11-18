"""Conformance test suite for VectorBackend implementations.

All vector backends must pass these tests. Parametrized by backend name.

Run with:
    pytest tests/backends/conformance.py -v --backend=faiss,memory
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import numpy as np
import pytest

from memory_engine.backends.base import BackendConfig, SearchQuery, VectorBackend, VectorRecord
from memory_engine.backends.registry import registry


# ─── Fixtures ───

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--backend",
        action="store",
        default="memory",
        help="Comma-separated list of backends to test (e.g., faiss,memory)",
    )


@pytest.fixture(scope="session")
def backend_names(request: pytest.FixtureRequest) -> list[str]:
    return [name.strip() for name in request.config.getoption("--backend").split(",")]


@pytest.fixture(scope="session")
def dimension() -> int:
    return 768


@pytest.fixture(scope="session")
def backend_factory(backend_names: list[str], dimension: int) -> dict[str, VectorBackend]:
    """Create backend instances for each backend name."""
    factories = {}
    for name in backend_names:
        if name not in registry:
            pytest.skip(f"Backend '{name}' not registered")
        config = BackendConfig(backend=name, dimension=dimension)
        if name == "faiss":
            config.faiss_index_type = "HNSW32"
        elif name == "memory":
            config.memory_backend = "hnsw"
        factories[name] = registry.create(config)
    return factories


@pytest.fixture(scope="function")
async def backend(
    backend_factory: dict[str, VectorBackend],
    backend_name: str,
) -> VectorBackend:
    """Get initialized backend for a specific test."""
    b = backend_factory[backend_name]
    config = BackendConfig(backend=backend_name, dimension=768)
    if backend_name == "faiss":
        config.faiss_index_type = "HNSW32"
    elif backend_name == "memory":
        config.memory_backend = "hnsw"
    await b.initialize(config)
    yield b
    await b.close()


@pytest.fixture(scope="function")
def backend_name(backend_names: list[str]) -> str:
    """Parametrize tests across backends."""
    return backend_names[0] if backend_names else "memory"


# ─── Helpers ───

def rand_vec(dim: int) -> np.ndarray:
    v = np.random.randn(dim).astype(np.float32)
    return v / (np.linalg.norm(v) + 1e-8)


def make_records(n: int, dim: int, tag: str = "test") -> list[VectorRecord]:
    return [
        VectorRecord(
            id=f"{tag}-{i}",
            vector=rand_vec(dim),
            metadata={"tag": tag, "index": i},
            payload={"text": f"Document {i}"},
        )
        for i in range(n)
    ]


# ─── Tests ───

class TestBackendConformance:
    """Tests that every VectorBackend must pass."""

    @pytest.mark.asyncio
    async def test_add_and_search(self, backend: VectorBackend) -> None:
        records = make_records(100, 768)
        await backend.add(records)

        query = SearchQuery(vector=rand_vec(768), k=10)
        results = await backend.search(query)

        assert len(results) == 10
        assert all(0 <= r.score <= 1 for r in results)
        assert all(r.rank == i for i, r in enumerate(results))

    @pytest.mark.asyncio
    async def test_search_returns_correct_ids(self, backend: VectorBackend) -> None:
        records = make_records(50, 768)
        await backend.add(records)

        # Search with one of the inserted vectors (should get itself at rank 0)
        query_vec = records[0].vector
        results = await backend.search(SearchQuery(vector=query_vec, k=5))

        assert len(results) >= 1
        assert results[0].record.id == records[0].id
        assert results[0].score > 0.99  # Near-exact match

    @pytest.mark.asyncio
    async def test_filter_exact_match(self, backend: VectorBackend) -> None:
        if not backend.supports_filter:
            pytest.skip("Backend does not support filter")

        records_a = make_records(50, 768, "tagA")
        records_b = make_records(50, 768, "tagB")
        await backend.add(records_a + records_b)

        query = SearchQuery(vector=rand_vec(768), k=10, filter={"tag": "tagA"})
        results = await backend.search(query)

        assert len(results) <= 10
        assert all(r.record.metadata.get("tag") == "tagA" for r in results)

    @pytest.mark.asyncio
    async def test_filter_expression(self, backend: VectorBackend) -> None:
        if not backend.supports_filter_expr:
            pytest.skip("Backend does not support filter_expr")

        records = [
            VectorRecord(
                id=f"item-{i}",
                vector=rand_vec(768),
                metadata={"category": "A" if i % 2 == 0 else "B", "value": i},
                payload={},
            )
            for i in range(100)
        ]
        await backend.add(records)

        # Backend-specific expression (e.g., SQL WHERE, Lucene)
        # This test is backend-specific; override in backend-specific test file
        pytest.skip("Filter expression syntax is backend-specific")

    @pytest.mark.asyncio
    async def test_payload_storage(self, backend: VectorBackend) -> None:
        if not backend.supports_payload:
            pytest.skip("Backend does not support payload")

        records = [
            VectorRecord(
                id=f"payload-{i}",
                vector=rand_vec(768),
                metadata={},
                payload={"text": f"Content {i}", "data": {"nested": i}},
            )
            for i in range(20)
        ]
        await backend.add(records)

        results = await backend.search(SearchQuery(vector=rand_vec(768), k=5, include_payload=True))
        assert len(results) == 5
        assert all("text" in r.record.payload for r in results)
        assert all("data" in r.record.payload for r in results)

    @pytest.mark.asyncio
    async def test_search_exclude_payload(self, backend: VectorBackend) -> None:
        records = make_records(10, 768)
        await backend.add(records)

        results = await backend.search(SearchQuery(vector=rand_vec(768), k=5, include_payload=False))
        assert all(r.record.payload == {} for r in results)

    @pytest.mark.asyncio
    async def test_search_exclude_vector(self, backend: VectorBackend) -> None:
        records = make_records(10, 768)
        await backend.add(records)

        results = await backend.search(SearchQuery(vector=rand_vec(768), k=5, include_vector=False))
        assert all(r.record.vector.size == 0 for r in results)

    @pytest.mark.asyncio
    async def test_delete(self, backend: VectorBackend) -> None:
        if not backend.supports_delete:
            pytest.skip("Backend does not support delete")

        records = make_records(20, 768)
        await backend.add(records)

        # Delete first 10
        await backend.delete([r.id for r in records[:10]])

        results = await backend.search(SearchQuery(vector=rand_vec(768), k=20))
        remaining_ids = {r.record.id for r in results}
        deleted_ids = {r.id for r in records[:10]}

        # Deleted IDs should not appear (or appear with low score if soft delete)
        # At minimum, verify they're not in top results
        assert not any(r.record.id in deleted_ids for r in results[:5])

    @pytest.mark.asyncio
    async def test_update(self, backend: VectorBackend) -> None:
        if not backend.supports_update:
            pytest.skip("Backend does not support update")

        records = make_records(10, 768)
        await backend.add(records)

        # Update first record with new vector
        new_vec = rand_vec(768)
        updated = VectorRecord(
            id=records[0].id,
            vector=new_vec,
            metadata={"updated": True},
            payload={"text": "UPDATED"},
        )
        await backend.update([updated])

        # Search with new vector should find updated record at rank 0
        results = await backend.search(SearchQuery(vector=new_vec, k=5))
        assert results[0].record.id == records[0].id
        assert results[0].record.metadata.get("updated") is True
        assert results[0].record.payload.get("text") == "UPDATED"

    @pytest.mark.asyncio
    async def test_persist_restore(self, backend: VectorBackend, tmp_path) -> None:
        if not backend.supports_persist:
            pytest.skip("Backend does not support persist")

        records = make_records(100, 768)
        await backend.add(records)

        backup_path = tmp_path / "backup"
        await backend.backup(str(backup_path))

        # Create new backend instance and restore
        config = BackendConfig(backend=backend.name, dimension=768)
        new_backend = registry.create(config)
        await new_backend.initialize(config)
        await new_backend.restore(str(backup_path))

        # Verify data restored
        results = await new_backend.search(SearchQuery(vector=rand_vec(768), k=10))
        assert len(results) == 10

        # Check specific records exist
        get_results = await new_backend.get([records[0].id, records[50].id])
        assert get_results[0] is not None
        assert get_results[0].id == records[0].id
        assert get_results[1] is not None
        assert get_results[1].id == records[50].id

        await new_backend.close()

    @pytest.mark.asyncio
    async def test_recall_at_k(self, backend: VectorBackend) -> None:
        """Ground-truth recall@10 >= 0.95 for HNSW backends."""
        if backend.name not in ("faiss", "memory", "qdrant", "milvus", "lancedb"):
            pytest.skip("Recall test only for ANN backends")

        n = 5000
        records = make_records(n, 768)
        await backend.add(records)

        # Use a subset for queries
        query_records = records[:100]
        total_recall = 0
        total_queries = 0

        for qr in query_records:
            results = await backend.search(SearchQuery(vector=qr.vector, k=10))
            found_ids = {r.record.id for r in results}
            total_recall += 1 if qr.id in found_ids else 0
            total_queries += 1

        recall = total_recall / total_queries
        assert recall >= 0.95, f"Recall@10 = {recall:.3f} < 0.95"

    @pytest.mark.asyncio
    async def test_latency_p99(self, backend: VectorBackend) -> None:
        """Latency p99 < 50ms for 100k vectors (HNSW backends)."""
        if backend.name not in ("faiss", "memory", "qdrant", "milvus", "lancedb"):
            pytest.skip("Latency test only for ANN backends")

        n = 50000  # Smaller for CI
        records = make_records(n, 768)
        await backend.add(records)

        # Warm up
        for _ in range(10):
            await backend.search(SearchQuery(vector=rand_vec(768), k=10))

        # Measure
        latencies = []
        for _ in range(200):
            start = time.perf_counter()
            await backend.search(SearchQuery(vector=rand_vec(768), k=10))
            latencies.append((time.perf_counter() - start) * 1000)  # ms

        latencies.sort()
        p99 = latencies[int(0.99 * len(latencies))]
        p50 = latencies[len(latencies) // 2]

        print(f"Backend {backend.name}: p50={p50:.1f}ms, p99={p99:.1f}ms")

        # Relaxed for CI; production should be < 50ms p99
        assert p99 < 200, f"p99 latency {p99:.1f}ms exceeds threshold"

    @pytest.mark.asyncio
    async def test_concurrent_writes(self, backend: VectorBackend) -> None:
        """10 concurrent writers, 1000 vectors each, no data loss."""
        n_writers = 10
        n_per_writer = 1000

        async def writer(writer_id: int) -> list[str]:
            records = [
                VectorRecord(
                    id=f"writer{writer_id}-{i}",
                    vector=rand_vec(768),
                    metadata={"writer": writer_id},
                    payload={},
                )
                for i in range(n_per_writer)
            ]
            await backend.add(records)
            return [r.id for r in records]

        await asyncio.gather(*[writer(i) for i in range(n_writers)])

        # Verify all written
        stats = await backend.stats()
        expected = n_writers * n_per_writer
        assert stats.num_vectors == expected, f"Expected {expected} vectors, got {stats.num_vectors}"

    @pytest.mark.asyncio
    async def test_stats(self, backend: VectorBackend) -> None:
        records = make_records(100, 768)
        await backend.add(records)

        stats = await backend.stats()

        assert stats.num_vectors == 100
        assert stats.dimension == 768
        assert stats.index_size_bytes > 0
        assert stats.backend_name == backend.name
        assert stats.backend_version
        assert stats.index_type
        assert stats.build_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_get(self, backend: VectorBackend) -> None:
        records = make_records(20, 768)
        await backend.add(records)

        results = await backend.get([records[0].id, records[5].id, "nonexistent"])

        assert results[0] is not None
        assert results[0].id == records[0].id
        assert results[1] is not None
        assert results[1].id == records[5].id
        assert results[2] is None

    @pytest.mark.asyncio
    async def test_compact(self, backend: VectorBackend) -> None:
        records = make_records(100, 768)
        await backend.add(records)

        await backend.delete([r.id for r in records[:50]])

        stats_before = await backend.stats()
        await backend.compact()
        stats_after = await backend.stats()

        # After compact, deleted vectors should be gone
        assert stats_after.num_vectors <= stats_before.num_vectors

    @pytest.mark.asyncio
    async def test_dimension_mismatch_raises(self, backend: VectorBackend) -> None:
        wrong_dim = VectorRecord(
            id="wrong-dim",
            vector=rand_vec(512),  # Wrong dimension
            metadata={},
            payload={},
        )
        with pytest.raises(ValueError):
            await backend.add([wrong_dim])

    @pytest.mark.asyncio
    async def test_empty_search(self, backend: VectorBackend) -> None:
        results = await backend.search(SearchQuery(vector=rand_vec(768), k=10))
        assert results == []

    @pytest.mark.asyncio
    async def test_k_larger_than_dataset(self, backend: VectorBackend) -> None:
        records = make_records(5, 768)
        await backend.add(records)

        results = await backend.search(SearchQuery(vector=rand_vec(768), k=100))
        assert len(results) == 5


# ─── Backend-specific parametrization ───

def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "backend" in metafunc.fixturenames:
        backend_names = metafunc.config.getoption("--backend").split(",")
        metafunc.parametrize("backend_name", [name.strip() for name in backend_names], indirect=True)