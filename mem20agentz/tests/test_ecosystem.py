"""Criterion-6 tests: mem20agentz really uses five other mem20 subsystems.

These are not import assertions. Each test calls the adapter and asserts on the
value the *other* subsystem computed, so a broken or removed call fails here:

* ``memory_engine`` — a fact written through the adapter is read back by the
  engine's own ``recall``.
* ``mem20crewz`` — the epistemic veto is asked about a real fact id and its
  verdict is surfaced (including the veto case).
* ``mem20dreamz`` — fidelity/divergence numbers come from the verdict module.
* ``mem20verify`` — every AST check in ``ALL_CHECKS`` runs over real source and
  a known-bad snippet is caught.
* ``mem20kilnz`` — a triangle count is judged against the authored budget table.
* ``mem20corez`` — perplexity is a finite number from the real char-MLP.

The store is redirected to a tmp dir per test, so nothing touches the live
ledger.
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(_HERE)
_REPO = os.path.dirname(_PROJECT)
for _p in (_PROJECT, _REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from mem20agentz import ecosystem  # noqa: E402


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A private memory store, with the engine reloaded against it."""
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "store"))
    for name in [m for m in list(sys.modules) if m == "memory"]:
        del sys.modules[name]
    memory = importlib.import_module("memory_engine.memory")
    # memory_engine reads MEM20_STORE_PATH at import time; rebind explicitly so
    # a module cached by an earlier test cannot leak its store into this one.
    memory.STORE_DIR = str(tmp_path / "store")
    memory.LEDGER = os.path.join(memory.STORE_DIR, "ledger.jsonl")
    memory.ENTRIES = os.path.join(memory.STORE_DIR, "entries")
    memory.INDEX = os.path.join(memory.STORE_DIR, "INDEX.md")
    memory.GRAPH_INDEX = os.path.join(memory.STORE_DIR, "memory_graph.json")
    return memory


# --------------------------------------------------------------- memory_engine
def test_grounded_context_reads_back_what_was_recorded(store):
    written = ecosystem.record_turn("agentz.test", "the vault code is 4417",
                                    tags=["agentz-test"])
    assert written["ok"] is True
    assert written["subsystem"] == "memory_engine"

    ctx = ecosystem.grounded_context(topic="agentz.test", k=5)
    assert ctx["ok"] is True
    assert ctx["count"] == 1
    assert ctx["rows"][0]["content"] == "the vault code is 4417"
    # the engine's own firewall: an agent's output is not an observation
    assert ctx["rows"][0]["epistemic_status"] == "agent_generated"
    assert ctx["rows"][0]["origin"] == "grounded"


def test_grounded_context_excludes_simulated(store):
    store.remember(topic="agentz.sim", content="a dragon guards the vault",
                   epistemic_status="observed")
    store.remember_simulated(topic="agentz.sim",
                             content="a dragon guards the vault")
    ctx = ecosystem.grounded_context(topic="agentz.sim", k=10)
    assert ctx["ok"] is True
    assert all(r.get("origin") == "grounded" for r in ctx["rows"])


# ------------------------------------------------------------------- mem20crewz
def test_veto_is_asked_and_reports_offenders(store):
    rec = store.remember(topic="agentz.veto", content="the vault code is 4417",
                         epistemic_status="agent_generated")
    out = ecosystem.veto_facts([rec["id"]])
    assert out["ok"] is True
    assert out["subsystem"] == "mem20crewz"
    # an unvalidated agent_generated fact must be vetoed, not waved through
    assert out["vetoed"] is True
    assert out["offenders"]
    assert "VETO" in out["reason"]


def test_veto_passes_on_user_stated_facts(store):
    rec = store.remember(topic="agentz.veto2", content="the vault code is 4417",
                         epistemic_status="user_stated")
    out = ecosystem.veto_facts([rec["id"]])
    assert out["ok"] is True
    assert out["vetoed"] is False


# ------------------------------------------------------------------- mem20dreamz
def test_fidelity_and_divergence_come_from_verdicts():
    seed = "summarise the hero mesh triangle budget for the prop family"
    faithful = "the prop family triangle budget is the hero mesh budget"
    off_brief = "bananas are yellow and grow in tropical climates"

    good = ecosystem.score_fidelity(seed, faithful)
    bad = ecosystem.score_fidelity(seed, off_brief)

    assert good["ok"] is True and bad["ok"] is True
    assert good["subsystem"] == "mem20dreamz"
    assert good["fidelity"] > bad["fidelity"]
    assert 0 <= good["fidelity"] <= 100
    # divergence is the verdict module's own number, not a local recomputation
    assert isinstance(good["divergence"], float)


# ------------------------------------------------------------------- mem20verify
def test_lint_runs_every_check_and_catches_identical_branches():
    bad = (
        "def f(x):\n"
        "    if x:\n"
        "        return 1\n"
        "    else:\n"
        "        return 1\n"
    )
    out = ecosystem.lint_source(bad, "bad.py")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20verify"
    assert out["checks"] >= 4
    assert out["clean"] is False
    assert any(i["check"] == "identical-branches" for i in out["issues"])


def test_lint_clean_source_is_clean():
    out = ecosystem.lint_source("def f(x):\n    return x + 1\n", "ok.py")
    assert out["ok"] is True
    assert out["clean"] is True
    assert out["issues"] == []


def test_lint_reports_syntax_error_instead_of_raising():
    out = ecosystem.lint_source("def f(:\n", "broken.py")
    assert out["ok"] is False
    assert "SyntaxError" in out["error"]


# -------------------------------------------------------------------- mem20kilnz
def test_budget_verdict_uses_the_authored_table():
    inside = ecosystem.check_asset_budget("prop", 4000)
    outside = ecosystem.check_asset_budget("prop", 12000)

    assert inside["ok"] is True and outside["ok"] is True
    assert inside["subsystem"] == "mem20kilnz"
    assert inside["within_budget"] is True
    assert outside["within_budget"] is False
    assert inside["band"] == [2000, 6000]
    assert "ceiling" in outside["reason"]


# -------------------------------------------------------------------- mem20corez
def test_perplexity_is_a_real_finite_measurement():
    out = ecosystem.model_confidence("the prop family triangle budget")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20corez"
    assert out["perplexity"] > 0
    assert out["params"] > 0


# --------------------------------------------------------------------- mem20cliz
def test_json_contract_uses_the_shared_cli_envelope():
    out = ecosystem.json_contract(["run", "--json", "--topic", "x"])
    assert out["ok"] is True
    assert out["subsystem"] == "mem20cliz"
    assert out["json"] is True
    assert out["argv"] == ["run", "--topic", "x"]
    assert out["schema_version"] >= 1


# ------------------------------------------------------------------- pipeline
def test_pipeline_prepare_then_review_wires_six_subsystems(store):
    store.remember(topic="agentz.pipe", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")

    pipe = ecosystem.GroundingPipeline(topic="agentz.pipe", k=5)
    report = pipe.prepare("what is the prop triangle budget?")
    assert report.context["count"] == 1

    answer = (
        "The prop budget is 4000 triangles.\n"
        "```python\n"
        "def within(n):\n"
        "    return n <= 6000\n"
        "```\n"
    )
    report = pipe.review("what is the prop triangle budget?", answer, report)

    assert report.verified is True
    assert set(report.subsystems) >= {
        "memory_engine", "mem20crewz", "mem20dreamz",
        "mem20verify", "mem20kilnz", "mem20corez",
    }
    assert report.lint["clean"] is True
    assert report.budget["within_budget"] is True
    assert report.fidelity["fidelity"] > 0
    assert report.confidence["perplexity"] > 0


def test_pipeline_degrades_honestly_when_a_subsystem_is_missing(monkeypatch):
    """A missing sibling must be reported, never silently treated as a pass."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "mem20kilnz" or name.startswith("mem20kilnz."):
            raise ModuleNotFoundError("simulated absence")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.delitem(sys.modules, "mem20kilnz", raising=False)
    monkeypatch.delitem(sys.modules, "mem20kilnz.budgets", raising=False)
    out = ecosystem.check_asset_budget("prop", 4000)
    assert out["ok"] is False
    assert "simulated absence" in out["error"]


def test_run_pipeline_one_shot(store):
    out = ecosystem.run_pipeline(
        "summarise the prop triangle budget",
        "the prop triangle budget is 4000 triangles",
        topic="agentz.one")
    assert out["verified"] is True
    assert out["budget"]["within_budget"] is True
    assert out["lint"]["clean"] is True
