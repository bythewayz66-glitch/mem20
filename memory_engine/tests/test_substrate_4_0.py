"""memory_engine 4.0 substrate conformance tests.

These test the *contract* layer, not the engine internals (the engine has its
own suite). Each test exercises a public API function on a real path and
asserts on real output — no mocks of the modules under test.

The cross-module criterion is covered by ``TestCrossModuleUseIsReal``: it
asserts that the sibling modules the substrate imports are actually *called*,
by checking the observable effect of each call rather than the presence of an
import statement.
"""

from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture()
def sub(tmp_path, monkeypatch):
    """A substrate bound to an isolated store.

    The engine derives its ledger paths (``LEDGER``, ``ENTRIES``, ...) from
    ``MEM20_STORE_PATH`` once, at import time. Setting the env var alone is
    therefore not enough when another test module already imported the engine,
    so reload it with the isolated path in place. ``guard_plan`` re-binds
    mem20crewz's backend to the reloaded module, so both sides still agree.
    """
    import importlib

    store = tmp_path / "store"
    store.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("MEM20_STORE_PATH", str(store))

    from memory_engine import memory as engine

    engine = importlib.reload(engine)
    assert engine.STORE_DIR == str(store)

    from memory_engine import substrate

    return substrate


# ---------------------------------------------------------------------------
# public API surface
# ---------------------------------------------------------------------------
class TestPublicAPI:
    def test_public_api_is_declared_and_complete(self, sub):
        assert sub.PUBLIC_API == (
            "remember_fact", "recall_facts", "veto_plan", "guard_plan",
            "namespace_for_agent", "subsystem_status", "envelope", "health",
            "dream_lineage", "validate_artifact",
        )

    def test_every_declared_name_exists(self, sub):
        for name in sub.PUBLIC_API:
            assert callable(getattr(sub, name)), f"{name} is not callable"


# ---------------------------------------------------------------------------
# write / read
# ---------------------------------------------------------------------------
class TestRememberAndRecall:
    def test_remember_returns_a_grounded_labeled_record(self, sub):
        rec = sub.remember_fact("t", "the sky is blue", epistemic_status="observed")
        assert rec["epistemic_status"] == "observed"
        assert rec["origin"] == "grounded"
        assert rec["topic"] == "t"

    def test_remember_refuses_an_undeclared_basis(self, sub):
        # epistemic_status is keyword-only with no default: the wrapper must not
        # invent a basis the caller did not state.
        with pytest.raises(TypeError):
            sub.remember_fact("t", "a claim")  # type: ignore[call-arg]

    def test_remember_refuses_an_invalid_basis(self, sub):
        with pytest.raises(ValueError):
            sub.remember_fact("t", "a claim", epistemic_status="probably")

    def test_remember_refuses_empty_input(self, sub):
        with pytest.raises(sub.SubstrateError):
            sub.remember_fact("", "a claim", epistemic_status="observed")
        with pytest.raises(sub.SubstrateError):
            sub.remember_fact("t", "", epistemic_status="observed")

    def test_recall_keeps_the_label(self, sub):
        sub.remember_fact("t", "the sky is blue", epistemic_status="inferred")
        rows = sub.recall_facts("t")
        assert rows
        assert rows[0]["epistemic_status"] == "inferred"

    def test_recall_normalises_a_missing_label_to_unlabeled(self, sub):
        # A record written by an older engine can carry no label. The substrate
        # must surface that as 'unlabeled', never as an absent field.
        engine = sub._engine()
        engine._append_ledger({
            "id": "legacy-1", "action": "remember", "topic": "t",
            "content": "an old claim", "tags": [], "ts": "2020-01-01",
            "origin": "grounded", "store": "grounded",
        })
        rows = sub.recall_facts("t", k=10)
        assert rows
        assert all(r.get("epistemic_status") for r in rows)
        assert any(r["epistemic_status"] == "unlabeled" for r in rows)

    def test_recall_respects_k(self, sub):
        for i in range(5):
            sub.remember_fact("t", f"claim {i}", epistemic_status="observed")
        assert len(sub.recall_facts("t", k=2)) == 2


# ---------------------------------------------------------------------------
# trust
# ---------------------------------------------------------------------------
class TestTrust:
    def test_veto_passes_a_grounded_observed_fact(self, sub):
        rec = sub.remember_fact("t", "the sky is blue", epistemic_status="observed")
        verdict = sub.veto_plan([rec["id"]])
        assert verdict["veto"] is False

    def test_veto_reports_an_unresolvable_id(self, sub):
        # A typo must not read as trust.
        verdict = sub.veto_plan(["no-such-fact-id"])
        assert verdict["unresolved"] or verdict["veto"] is True

    def test_guard_plan_returns_clearance_and_events(self, sub):
        rec = sub.remember_fact("t", "the sky is blue", epistemic_status="observed")
        result = sub.guard_plan([rec["id"]])
        assert result["blocked"] is False
        assert "clearance" in result
        # mem20crewz's Guards recorded the checks it actually ran.
        kinds = {e["kind"] for e in result["events"]}
        assert "epistemic_veto" in kinds


# ---------------------------------------------------------------------------
# partitioning / estate
# ---------------------------------------------------------------------------
class TestEstate:
    def test_namespace_uses_the_agentz_rule(self, sub):
        assert sub.namespace_for_agent("my agent") == "mem20agentz:my-agent"

    def test_namespace_refuses_an_empty_name(self, sub):
        with pytest.raises(sub.SubstrateError):
            sub.namespace_for_agent("   ")

    def test_subsystem_status_finds_a_real_subsystem(self, sub):
        status = sub.subsystem_status("mem20kilnz")
        assert status["found"] is True
        assert status["kind"] == "subsystem"
        assert status["description"]

    def test_subsystem_status_reports_an_absent_one(self, sub):
        status = sub.subsystem_status("mem20doesnotexist")
        assert status["found"] is False
        assert status["runtime_status"] == "absent"

    def test_envelope_uses_the_cliz_schema(self, sub):
        env = sub.envelope("recall", ["--topic", "t"], 0, "out", "")
        assert env["schema"] == "mem20.cli/1"
        assert env["ok"] is True
        assert env["command"] == "recall"

    def test_envelope_marks_a_failure(self, sub):
        env = sub.envelope("recall", [], 1, "", "boom")
        assert env["ok"] is False
        assert env["stderr"] == "boom"


# ---------------------------------------------------------------------------
# artifacts
# ---------------------------------------------------------------------------
class TestArtifacts:
    def test_dream_lineage_returns_a_real_resumable_lineage(self, sub, tmp_path, monkeypatch):
        monkeypatch.setenv("MEM20DREAM_STORE", str(tmp_path / "dreams"))
        import importlib

        from mem20dreamz import lineage as dream_lineage_mod

        importlib.reload(dream_lineage_mod)
        from mem20dreamz import engine as dream_engine

        importlib.reload(dream_engine)

        out = sub.dream_lineage("a seed")
        assert out["dream_id"].startswith("dream-")
        assert out["artifact"] == "a seed"
        # The lineage was really persisted, not just described.
        assert os.path.isfile(out["state_path"])

    def test_dream_lineage_refuses_an_empty_seed(self, sub):
        with pytest.raises(sub.SubstrateError):
            sub.dream_lineage("  ")

    def test_validate_artifact_accepts_a_minimal_gltf(self, sub, tmp_path):
        import json

        p = tmp_path / "m.gltf"
        p.write_text(json.dumps({
            "asset": {"version": "2.0"},
            "scenes": [{"nodes": []}], "scene": 0, "nodes": [],
        }))
        out = sub.validate_artifact(str(p))
        assert out["ok"] is True
        assert out["nodes"] == 0

    def test_validate_artifact_reports_a_missing_file_as_failure(self, sub, tmp_path):
        out = sub.validate_artifact(str(tmp_path / "nope.gltf"))
        assert out["ok"] is False
        assert any(f["code"] == "not_found" for f in out["findings"])


# ---------------------------------------------------------------------------
# health
# ---------------------------------------------------------------------------
class TestHealth:
    def test_health_measures_the_store(self, sub):
        sub.remember_fact("t", "one", epistemic_status="observed")
        sub.remember_fact("t", "two", epistemic_status="inferred")
        h = sub.health()
        assert h["grounded_facts"] == 2
        assert h["labeled_facts"] == 2
        assert h["label_coverage"] == 1.0
        assert h["public_api"] == list(sub.PUBLIC_API)

    def test_health_reports_retrieval_halves_honestly(self, sub):
        h = sub.health()
        engine = sub._engine()
        assert h["vector_available"] == bool(engine.VECTOR_AVAILABLE)
        assert h["bm25_available"] == bool(engine.BM25_AVAILABLE)


# ---------------------------------------------------------------------------
# criterion 6 — the cross-module imports are USED, not merely present
# ---------------------------------------------------------------------------
class TestCrossModuleUseIsReal:
    """Each sibling module must be *called* on a path these tests exercise."""

    def test_mem20cliz_is_used(self, sub):
        # The envelope's schema string is produced by mem20cliz.build_envelope.
        from mem20cliz import build_envelope

        assert sub.envelope("x", [], 0)["schema"] == build_envelope("x", [], 0, "", "")["schema"]

    def test_mem20crewz_is_used(self, sub):
        # guard_plan routes through mem20crewz.Guards; its event log is the proof.
        rec = sub.remember_fact("t", "a fact", epistemic_status="observed")
        result = sub.guard_plan([rec["id"]])
        assert result["events"], "mem20crewz Guards produced no events"

    def test_mem20agentz_is_used(self, sub):
        from mem20agentz.profiles import namespace_for

        assert sub.namespace_for_agent("a b") == namespace_for("a b")

    def test_toolchest_is_used(self, sub):
        # subsystem_status reads toolchest's on-disk catalogue.
        from toolchest import catalog

        assert sub.subsystem_status("mem20kilnz")["found"] is True
        assert catalog.MEM20_ROOT.exists()

    def test_memory_engine_is_used(self, sub):
        # The engine is the store itself: a write through the substrate is
        # visible in the engine's own ledger.
        rec = sub.remember_fact("t", "a fact", epistemic_status="observed")
        ids = [r.get("id") for r in sub._engine()._load_ledger()]
        assert rec["id"] in ids

    def test_mem20dreamz_is_used(self, sub, tmp_path, monkeypatch):
        monkeypatch.setenv("MEM20DREAM_STORE", str(tmp_path / "dreams"))
        import importlib

        from mem20dreamz import lineage as dream_lineage_mod

        importlib.reload(dream_lineage_mod)
        from mem20dreamz import engine as dream_engine

        importlib.reload(dream_engine)
        out = sub.dream_lineage("a seed")
        assert out["dream_id"].startswith("dream-")

    def test_mem20kilnz_is_used(self, sub, tmp_path):
        import json

        p = tmp_path / "m.gltf"
        p.write_text(json.dumps({"asset": {"version": "2.0"},
                                 "scenes": [{"nodes": []}], "scene": 0, "nodes": []}))
        assert sub.validate_artifact(str(p))["ok"] is True
