"""Criterion-6 tests: mem20crewz really uses five other mem20 subsystems.

Each test calls the adapter and asserts on the value the *other* subsystem
computed, so a broken or removed call fails here:

* ``memory_engine`` — a crew outcome recorded through the governor is read back
  by the engine's own ``recall`` and labelled ``agent_generated``.
* ``mem20verify`` — every AST check in ``ALL_CHECKS`` runs over crew code and a
  known-bad snippet is caught.
* ``mem20dreamz`` — fidelity/divergence come from the verdict module.
* ``mem20kilnz`` — a claimed triangle count is judged against the budget table.
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

import ecosystem  # noqa: E402


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
    store.remember(topic="crew.topic", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")
    out = ecosystem.grounded_context(topic="crew.topic")
    assert out["ok"] is True
    assert out["subsystem"] == "memory_engine"
    assert out["count"] == 1
    assert out["rows"][0]["content"] == "the prop budget is 4000 triangles"


def test_record_outcome_is_labelled_agent_generated(store):
    out = ecosystem.record_outcome("crew.done", "the crew produced a budget check")
    assert out["ok"] is True
    assert out["subsystem"] == "memory_engine"

    rows = store.recall(topic="crew.done", k=5)
    assert rows
    # an agent's output is not an observation, and the firewall must say so
    assert rows[0]["epistemic_status"] == "agent_generated"


# ------------------------------------------------------------------ mem20verify
def test_lint_runs_every_check_and_catches_identical_branches():
    bad = ("def f(x):\n"
           "    if x:\n"
           "        return 1\n"
           "    else:\n"
           "        return 1\n")
    out = ecosystem.lint_output(bad, "bad.py")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20verify"
    assert out["checks"] >= 4
    assert out["clean"] is False
    assert any(i["check"] == "identical-branches" for i in out["issues"])


def test_lint_clean_output_is_clean():
    out = ecosystem.lint_output("def f(x):\n    return x + 1\n", "ok.py")
    assert out["ok"] is True
    assert out["clean"] is True
    assert out["issues"] == []


# ----------------------------------------------------------------- mem20dreamz
def test_fidelity_separates_on_brief_from_off_brief_output():
    brief = "build the prop family triangle budget check"
    on_brief = "the prop family triangle budget check returns 4000"
    off_brief = "bananas grow in tropical climates"

    good = ecosystem.score_fidelity(brief, on_brief)
    bad = ecosystem.score_fidelity(brief, off_brief)

    assert good["ok"] is True and bad["ok"] is True
    assert good["subsystem"] == "mem20dreamz"
    assert good["fidelity"] > bad["fidelity"]
    assert isinstance(good["divergence"], float)


# ----------------------------------------------------------------- mem20kilnz
def test_budget_verdict_uses_the_authored_table():
    inside = ecosystem.check_asset_budget("prop", 4000)
    outside = ecosystem.check_asset_budget("prop", 12000)

    assert inside["ok"] is True and outside["ok"] is True
    assert inside["subsystem"] == "mem20kilnz"
    assert inside["within_budget"] is True
    assert outside["within_budget"] is False
    assert inside["band"] == [2000, 6000]
    assert "ceiling" in outside["reason"]


# ----------------------------------------------------------------- mem20corez
def test_surprise_is_a_real_finite_measurement():
    out = ecosystem.output_surprise("the prop family triangle budget")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20corez"
    assert out["perplexity"] > 0
    assert out["params"] > 0


# ------------------------------------------------------------------ mem20cliz
def test_cli_envelope_is_the_shared_fleet_envelope():
    out = ecosystem.cli_envelope("govern", ["govern", "--json"], 0, "ok")
    assert out["ok"] is True
    assert out["subsystem"] == "mem20cliz"
    assert out["json"] is True
    assert out["envelope"]["schema"] == "mem20.cli/1"


# ------------------------------------------------------------------- governor
def test_governor_prepare_then_judge_wires_five_subsystems(store):
    store.remember(topic="crew.pipe", content="the prop budget is 4000 triangles",
                   epistemic_status="user_stated")

    gov = ecosystem.CrewGovernor(topic="crew.pipe")
    report = gov.prepare()
    assert report.context["count"] == 1

    output = ("The prop budget is 4000 triangles.\n"
              "```python\n"
              "def within(n):\n"
              "    return n <= 6000\n"
              "```\n")
    report = gov.judge("what is the prop triangle budget?", output,
                       report=report)

    assert report.clear is True
    assert set(report.subsystems) >= {
        "memory_engine", "mem20verify", "mem20dreamz", "mem20kilnz",
        "mem20corez",
    }
    assert report.lint["clean"] is True
    assert report.budget["within_budget"] is True
    assert report.fidelity["fidelity"] > 0
    assert report.surprise["perplexity"] > 0


def test_governor_marks_a_dirty_output_dirty(store):
    gov = ecosystem.CrewGovernor(topic="crew.bad")
    report = gov.prepare()
    bad = ("```python\n"
           "def f(x):\n"
           "    if x:\n"
           "        return 1\n"
           "    else:\n"
           "        return 1\n"
           "```\n")
    report = gov.judge("write a function", bad, report=report)
    assert report.lint["clean"] is False
    # the governor itself ran fine; the *output* is what failed its check
    assert report.clear is True


def test_governor_degrades_honestly_when_a_subsystem_is_missing(monkeypatch):
    """A missing sibling must be reported, never silently treated as a pass."""
    class BrokenDeps:
        def __getattr__(self, name):
            raise ImportError("simulated absence")

    monkeypatch.setattr(ecosystem, "_DEPS", BrokenDeps())
    out = ecosystem.check_asset_budget("prop", 4000)
    assert out["ok"] is False
    assert "simulated absence" in out["error"]


def test_run_governor_one_shot(store):
    out = ecosystem.run_governor(
        "summarise the prop triangle budget",
        "the prop triangle budget is 4000 triangles",
        topic="crew.one")
    assert out["clear"] is True
    assert out["budget"]["within_budget"] is True
    assert out["lint"]["clean"] is True
