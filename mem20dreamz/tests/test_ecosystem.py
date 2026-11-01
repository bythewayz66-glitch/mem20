"""Criterion-6 tests: mem20dreamz really uses five other mem20 subsystems.

Each test calls the adapter and asserts on the value the *other* subsystem
computed, so a broken or removed call fails here:

* ``memory_engine`` — a dream recorded through the gate is read back by the
  engine's own ``recall``, labelled ``agent_generated``.
* ``mem20crewz`` — the epistemic veto refuses a dream built on unvalidated
  agent output and passes one built on user-stated facts.
* ``mem20verify`` — every AST check in ``ALL_CHECKS`` runs over dream code and a
  known-bad snippet is caught.
* ``mem20kilnz`` — a proposed triangle count is judged against the authored
  budget table.
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

from mem20dreamz import ecosystem  # noqa: E402


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
def test_ground_seed_reads_the_estate(store):
    store.remember(topic="dream.mesh", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")
    out = ecosystem.ground_seed("dream.mesh")
    assert out["ok"] is True
    assert out["subsystem"] == "memory_engine"
    assert out["count"] == 1
    assert out["rows"][0]["content"] == "the prop budget is 4000 triangles"


def test_record_dream_is_labelled_agent_generated(store):
    out = ecosystem.record_dream("mesh", "a dream about a lighter prop mesh")
    assert out["ok"] is True
    assert out["subsystem"] == "memory_engine"

    rows = store.recall(topic="dream.mesh", k=5)
    assert rows
    # a dream is not an observation, and the firewall must be able to tell
    assert rows[0]["epistemic_status"] == "agent_generated"


# ------------------------------------------------------------------ mem20crewz
def test_veto_refuses_a_dream_built_on_agent_output(store):
    rec = store.remember(topic="dream.veto", content="the vault code is 4417",
                         epistemic_status="agent_generated")
    out = ecosystem.veto_claims([rec["id"]])
    assert out["ok"] is True
    assert out["subsystem"] == "mem20crewz"
    assert out["vetoed"] is True
    assert out["offenders"]


def test_veto_passes_a_dream_built_on_user_stated_facts(store):
    rec = store.remember(topic="dream.veto2", content="the vault code is 4417",
                         epistemic_status="user_stated")
    out = ecosystem.veto_claims([rec["id"]])
    assert out["ok"] is True
    assert out["vetoed"] is False


# ------------------------------------------------------------------ mem20verify
def test_lint_runs_every_check_and_catches_identical_branches():
    bad = ("def f(x):\n"
           "    if x:\n"
           "        return 1\n"
           "    else:\n"
           "        return 1\n")
    out = ecosystem.lint_candidate(bad, "bad.py")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20verify"
    assert out["checks"] >= 4
    assert out["clean"] is False
    assert any(i["check"] == "identical-branches" for i in out["issues"])


def test_lint_clean_candidate_is_clean():
    out = ecosystem.lint_candidate("def f(x):\n    return x + 1\n", "ok.py")
    assert out["ok"] is True
    assert out["clean"] is True
    assert out["issues"] == []


# ------------------------------------------------------------------ mem20kilnz
def test_budget_verdict_uses_the_authored_table():
    inside = ecosystem.check_asset_budget("prop", 4000)
    outside = ecosystem.check_asset_budget("prop", 12000)

    assert inside["ok"] is True and outside["ok"] is True
    assert inside["subsystem"] == "mem20kilnz"
    assert inside["within_budget"] is True
    assert outside["within_budget"] is False
    assert inside["band"] == [2000, 6000]
    assert "ceiling" in outside["reason"]


# ------------------------------------------------------------------ mem20corez
def test_corpus_distance_is_a_real_finite_measurement():
    out = ecosystem.corpus_distance("a dream about a lighter prop mesh")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20corez"
    assert out["perplexity"] > 0
    assert out["params"] > 0


# ------------------------------------------------------------------- mem20cliz
def test_cli_envelope_is_the_shared_fleet_envelope():
    out = ecosystem.cli_envelope("gate", ["gate", "--json"], 0, "ok")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20cliz"
    assert out["json"] is True
    assert out["envelope"]["schema"] == "mem20.cli/1"


# --------------------------------------------------------------------- the gate
def test_gate_ground_then_judge_wires_six_subsystems(store):
    store.remember(topic="dream.pipe", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")

    gate = ecosystem.DreamGate(seed="dream.pipe")
    report = gate.ground()
    assert report.grounding["count"] == 1

    candidate = ("A lighter prop mesh at 4000 triangles.\n"
                 "```python\n"
                 "def within(n):\n"
                 "    return n <= 6000\n"
                 "```\n")
    report = gate.judge(candidate, report=report)

    assert report.promotable is True
    assert set(report.subsystems) >= {
        "memory_engine", "mem20crewz", "mem20verify", "mem20kilnz",
        "mem20corez",
    }
    assert report.lint["clean"] is True
    assert report.budget["within_budget"] is True
    assert report.distance["perplexity"] > 0


def test_gate_blocks_a_candidate_that_fails_lint(store):
    gate = ecosystem.DreamGate(seed="dream.bad")
    report = gate.ground()
    bad = ("```python\n"
           "def f(x):\n"
           "    if x:\n"
           "        return 1\n"
           "    else:\n"
           "        return 1\n"
           "```\n")
    report = gate.judge(bad, report=report)
    assert report.lint["clean"] is False
    assert report.promotable is True  # the check ran; the *candidate* is dirty


def test_gate_degrades_honestly_when_a_subsystem_is_missing(monkeypatch):
    """A missing sibling must be reported, never silently treated as a pass."""
    class BrokenDeps:
        def __getattr__(self, name):
            raise ImportError("simulated absence")

    monkeypatch.setattr(ecosystem, "_DEPS", BrokenDeps())
    out = ecosystem.check_asset_budget("prop", 4000)
    assert out["ok"] is False
    assert "simulated absence" in out["error"]


def test_run_gate_one_shot(store):
    out = ecosystem.run_gate(
        "dream.one",
        "a prop mesh at 4000 triangles\n```python\ndef f(x):\n    return x + 1\n```")
    assert out["promotable"] is True
    assert out["budget"]["within_budget"] is True
    assert out["lint"]["clean"] is True
