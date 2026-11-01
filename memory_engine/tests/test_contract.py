"""Contract tests for the memory_engine public surface (M0).

These tests FAIL on d99ab5d (before M0) and PASS after. They are the
executable definition of the seam: if a future change removes a name from
``__all__``, changes a return type, or lets the facade drift from the engine,
one of these goes red.

Run: python3 -m pytest memory_engine/tests/test_contract.py -q
"""

from __future__ import annotations

import inspect
import os
import sys
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

# Isolate the store BEFORE importing the engine (it resolves paths at import).
_STORE = tempfile.mkdtemp(prefix="mem20_contract_")
os.environ["MEM20_STORE_PATH"] = _STORE

import memory_engine  # noqa: E402
from memory_engine import (  # noqa: E402
    EPISTEMIC_STATUSES,
    UNLABELED,
    EngineConfig,
    Fact,
    MemoryEngine,
    MemoryEngineError,
)


# ---------------------------------------------------------------------------
# Surface declaration
# ---------------------------------------------------------------------------


class TestPublicSurface:
    def test_package_declares_all(self):
        """Before M0 __init__.py was 0 bytes: no __all__, no contract."""
        assert hasattr(memory_engine, "__all__")
        assert len(memory_engine.__all__) > 0

    def test_every_declared_name_resolves(self):
        """A name in __all__ that does not resolve is a broken promise."""
        missing = []
        for name in memory_engine.__all__:
            try:
                getattr(memory_engine, name)
            except AttributeError:
                missing.append(name)
        assert missing == [], f"declared but unresolvable: {missing}"

    def test_dir_matches_all(self):
        assert set(dir(memory_engine)) == set(memory_engine.__all__)

    def test_unknown_attribute_raises(self):
        with pytest.raises(AttributeError):
            memory_engine.definitely_not_a_real_name

    def test_version_is_declared(self):
        assert memory_engine.__version__ == "3.1.2"

    def test_epistemic_vocabulary_matches_engine(self):
        """The literal in api.py must equal the engine's list, or the contract lies."""
        from memory_engine import memory as engine

        assert tuple(engine.EPISTEMIC_STATUSES) == EPISTEMIC_STATUSES
        assert engine.UNLABELED == UNLABELED

    def test_engine_functions_are_reachable_from_package(self):
        """Consumers should not have to import memory_engine.memory directly."""
        for name in ("remember", "recall", "recall_at", "index_health", "status"):
            assert callable(getattr(memory_engine, name))


# ---------------------------------------------------------------------------
# Facade shape
# ---------------------------------------------------------------------------


class TestFacadeShape:
    def test_engine_constructs_without_touching_store(self):
        """Construction must not create or read the store."""
        from memory_engine import memory as engine

        eng = MemoryEngine()
        # conftest.py sets MEM20_STORE_PATH before the engine is imported, so
        # the engine's resolved path is authoritative, not this module's _STORE.
        assert eng.store_path == engine.STORE_DIR

    def test_remember_returns_fact_not_dict(self):
        eng = MemoryEngine()
        fact = eng.remember(
            "contract.shape",
            "the facade returns typed facts",
            epistemic_status="observed",
        )
        assert isinstance(fact, Fact)
        assert fact.topic == "contract.shape"
        assert fact.epistemic_status == "observed"
        assert fact.origin == "grounded"
        assert fact.id

    def test_fact_keeps_raw_record(self):
        eng = MemoryEngine()
        fact = eng.remember(
            "contract.raw", "raw record is preserved", epistemic_status="observed"
        )
        assert isinstance(fact.raw, dict)
        assert fact.raw["id"] == fact.id

    def test_recall_returns_list_of_facts(self):
        eng = MemoryEngine()
        eng.remember(
            "contract.recall", "recallable fact", epistemic_status="observed"
        )
        facts = eng.recall(topic="contract.recall")
        assert isinstance(facts, list)
        assert all(isinstance(f, Fact) for f in facts)
        assert any(f.topic == "contract.recall" for f in facts)

    def test_health_returns_report(self):
        from memory_engine import memory as engine

        eng = MemoryEngine()
        report = eng.health()
        assert report.store_path == engine.STORE_DIR
        assert isinstance(report.to_dict(), dict)
        assert "healthy" in report.to_dict()

    def test_health_on_missing_store_is_unhealthy_not_raising(self):
        """A readiness probe must answer, not crash."""
        cfg = EngineConfig.from_env().with_store(
            os.path.join(tempfile.mkdtemp(prefix="mem20_absent_"), "nope")
        )
        report = MemoryEngine(cfg).health()
        assert report.healthy is False
        assert report.ledger_records == 0

    def test_fact_is_trusted_reflects_status(self):
        eng = MemoryEngine()
        observed = eng.remember(
            "contract.trust", "observed claim", epistemic_status="observed"
        )
        imagined = eng.remember(
            "contract.trust", "imagined claim", epistemic_status="imagined"
        )
        assert observed.is_trusted is True
        assert imagined.is_trusted is False


# ---------------------------------------------------------------------------
# Facade does not reimplement the engine
# ---------------------------------------------------------------------------


class TestNoDrift:
    def test_facade_delegates_to_engine_module(self):
        """The facade must call the engine, not carry its own copy of the logic."""
        src = inspect.getsource(memory_engine.api)
        assert "self._engine.remember" in src
        assert "self._engine.recall" in src

    def test_facade_has_no_ledger_io(self):
        """A facade that opens the ledger itself would be a second implementation."""
        src = inspect.getsource(memory_engine.api)
        assert "open(" not in src
        assert "json.load" not in src


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    def test_legacy_import_path_still_works(self):
        """Existing consumers do `from memory_engine import memory as engine`."""
        from memory_engine import memory as engine

        assert callable(engine.remember)
        assert callable(engine.recall)

    def test_legacy_root_shim_still_works(self):
        """The repo-root memory.py shim re-exports the engine."""
        import memory as shim

        assert callable(shim.remember)
        assert callable(shim.recall)

    def test_typed_errors_keep_builtin_bases(self):
        """Old `except ValueError` handlers must keep catching."""
        from memory_engine import EpistemicStatusError, GroundedWriteRefused

        assert issubclass(EpistemicStatusError, ValueError)
        assert issubclass(GroundedWriteRefused, PermissionError)
        assert issubclass(MemoryEngineError, Exception)
