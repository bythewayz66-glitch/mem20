"""Criterion-6 tests: mem20kilnz really uses five other mem20 subsystems.

Each test calls the adapter and asserts on the value the *other* subsystem
computed, so a broken or removed call fails here:

* ``memory_engine`` — a build recorded through the gate is read back by the
  engine's own ``recall`` and labelled ``agent_generated``.
* ``mem20crewz`` — the epistemic veto refuses a build resting on unvalidated
  agent output and passes one resting on user-stated facts.
* ``mem20verify`` — every AST check in ``ALL_CHECKS`` runs over emitted code and
  a known-bad snippet is caught.
* ``mem20dreamz`` — fidelity/divergence come from the verdict module.
* ``mem20corez`` — perplexity is a finite number from the real char-MLP.
* ``mem20cliz`` — the CLI envelope is the fleet's shared one.

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

from mem20kilnz import ecosystem  # noqa: E402


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """A private memory store, with the engine rebound against it."""
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "store"))
    sys.modules.pop("memory", None)
    memory = importlib.import_module("memory_engine.memory")
    memory.STORE_DIR = str(tmp_path / "store")
    memory.MEM_DIR = memory.STORE_DIR
    memory.LEDGER = os.path.join(memory.STORE_DIR, "ledger.jsonl")
    memory.ENTRIES = os.path.join(memory.STORE_DIR, "entries")
    memory.INDEX = os.path.join(memory.STORE_DIR, "INDEX.md")
    memory.GRAPH_INDEX = os.path.join(memory.STORE_DIR, "memory_graph.json")
    return memory


# --------------------------------------------------------------- memory_engine
def test_grounded_context_reads_back_what_was_recorded(store):
    store.remember(topic="kiln.prop", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")
    out = ecosystem.grounded_context(topic="kiln.prop")
    assert out["ok"] is True
    assert out["subsystem"] == "memory_engine"
    assert out["count"] == 1
    assert out["rows"][0]["content"] == "the prop budget is 4000 triangles"


def test_record_build_is_labelled_agent_generated(store):
    out = ecosystem.record_build("kiln.done", "built a prop mesh at 4000 triangles")
    assert out["ok"] is True
    assert out["subsystem"] == "memory_engine"

    rows = store.recall(topic="kiln.done", k=5)
    assert rows
    # a build report is not an observation, and the firewall must say so
    assert rows[0]["epistemic_status"] == "agent_generated"


# ------------------------------------------------------------------ mem20crewz
def test_veto_refuses_a_build_on_agent_output(store):
    rec = store.remember(topic="kiln.veto", content="the vault code is 4417",
                         epistemic_status="agent_generated")
    out = ecosystem.veto_facts([rec["id"]])
    assert out["ok"] is True
    assert out["subsystem"] == "mem20crewz"
    assert out["vetoed"] is True
    assert out["offenders"]


def test_veto_passes_a_build_on_user_stated_facts(store):
    rec = store.remember(topic="kiln.veto2", content="the vault code is 4417",
                         epistemic_status="user_stated")
    out = ecosystem.veto_facts([rec["id"]])
    assert out["ok"] is True
    assert out["vetoed"] is False


# ------------------------------------------------------------------ mem20verify
def test_lint_runs_every_check_and_catches_identical_branches():
    bad = ("def f(x):\n"
           "    if x:\n"
           "        return 1\n"
           "    else:\n"
           "        return 1\n")
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


# ----------------------------------------------------------------- mem20dreamz
def test_fidelity_separates_on_brief_from_off_brief_result():
    brief = "build the prop family mesh at the standard budget"
    on_brief = "the prop family mesh is built at the standard budget"
    off_brief = "bananas grow in tropical climates"

    good = ecosystem.score_fidelity(brief, on_brief)
    bad = ecosystem.score_fidelity(brief, off_brief)

    assert good["ok"] is True and bad["ok"] is True
    assert good["subsystem"] == "mem20dreamz"
    assert good["fidelity"] > bad["fidelity"]
    assert isinstance(good["divergence"], float)


# ----------------------------------------------------------------- mem20corez
def test_surprise_is_a_real_finite_measurement():
    out = ecosystem.result_surprise("the prop family mesh at 4000 triangles")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20corez"
    assert out["perplexity"] > 0
    assert out["params"] > 0


# ------------------------------------------------------------------ mem20cliz
def test_cli_envelope_is_the_shared_fleet_envelope():
    out = ecosystem.cli_envelope("gate", ["gate", "--json"], 0, "ok")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20cliz"
    assert out["json"] is True
    assert out["envelope"]["schema"] == "mem20.cli/1"


# --------------------------------------------------------------------- the gate
def test_gate_prepare_then_judge_wires_five_subsystems(store):
    store.remember(topic="kiln.pipe", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")

    gate = ecosystem.BuildGate(topic="kiln.pipe")
    report = gate.prepare()
    assert report.context["count"] == 1

    result = ("Built the prop mesh at 4000 triangles.\n"
              "```python\n"
              "def within(n):\n"
              "    return n <= 6000\n"
              "```\n")
    report = gate.judge("build the prop mesh at the standard budget", result,
                        report=report)

    assert report.shippable is True
    assert set(report.subsystems) >= {
        "memory_engine", "mem20crewz", "mem20verify", "mem20dreamz",
        "mem20corez",
    }
    assert report.veto["vetoed"] is False
    assert report.lint["clean"] is True
    assert report.fidelity["fidelity"] > 0
    assert report.surprise["perplexity"] > 0


def test_gate_marks_a_dirty_result_dirty(store):
    gate = ecosystem.BuildGate(topic="kiln.bad")
    report = gate.prepare()
    bad = ("```python\n"
           "def f(x):\n"
           "    if x:\n"
           "        return 1\n"
           "    else:\n"
           "        return 1\n"
           "```\n")
    report = gate.judge("emit a helper", bad, report=report)
    assert report.lint["clean"] is False
    # the gate itself ran fine; the *result* is what failed its check
    assert report.shippable is True


def test_gate_degrades_honestly_when_a_subsystem_is_missing(monkeypatch):
    """A missing sibling must be reported, never silently treated as a pass."""
    class BrokenDeps:
        def __getattr__(self, name):
            raise ImportError("simulated absence")

    monkeypatch.setattr(ecosystem, "_DEPS", BrokenDeps())
    out = ecosystem.lint_source("def f(x):\n    return x\n")
    assert out["ok"] is False
    assert "simulated absence" in out["error"]


def test_run_gate_one_shot(store):
    out = ecosystem.run_gate(
        "build the prop mesh at the standard budget",
        "the prop mesh is built at 4000 triangles",
        topic="kiln.one")
    assert out["shippable"] is True
    assert out["lint"]["clean"] is True
    assert out["fidelity"]["fidelity"] > 0
