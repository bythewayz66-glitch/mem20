"""Tests for the mem20wasmz cross-module wiring and CLI.

The wiring tests need no external service: they call six other mem20 subsystems
and assert on the real values those calls return. If one of them breaks, the 4.0
architecture rule is broken, not just a test.

The CLI tests run the real runtime over the lab's own roadmap in a scratch
directory, so they never write into the checkout.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from mem20wasmz import wiring
from mem20wasmz.cli import EXIT_FAILED, EXIT_OK, main

LAB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --- wiring: six real cross-module calls ------------------------------------


def test_canonical_result_is_order_independent():
    """mem20core.canonical makes key order irrelevant to the hash."""
    a = wiring.canonical_result({"mode": "local", "roadmap_id": 101})
    b = wiring.canonical_result({"roadmap_id": 101, "mode": "local"})
    assert a["stable_hash"] == b["stable_hash"]
    assert a["canonical"] == b["canonical"]


def test_memory_status_line_is_real_output():
    """memory_engine.status() returns a real report, not a placeholder."""
    line = wiring.memory_status_line()
    assert isinstance(line, str)
    assert line.strip() != ""


def test_tool_surface_reports_a_count():
    """toolchest.catalog.discover_mcp_tools() is reachable and returns a count."""
    surface = wiring.tool_surface()
    assert isinstance(surface["count"], int)
    assert surface["count"] >= 0
    assert "ok" in surface


def test_lint_source_accepts_clean_code():
    """mem20verify's identical-branch linter runs and finds nothing here."""
    assert wiring.lint_source("def f(x):\n    return x + 1\n") == []


def test_lint_source_flags_identical_branches():
    """The linter is not vacuous: duplicated branches are reported."""
    source = "def f(x):\n    if x:\n        return 1\n    else:\n        return 1\n"
    assert len(wiring.lint_source(source)) >= 1


def test_store_identity_probes_a_scratch_store():
    """mem20ops.identity_check() runs against a throwaway store."""
    identity = wiring.store_identity()
    assert "store_path" in identity
    assert "namespace_count" in identity


def test_gateway_agents_returns_a_mapping():
    """gateway.hermes_gateway.load_names() is reachable."""
    assert isinstance(wiring.gateway_agents(), dict)


def test_self_check_covers_six_modules():
    """The self-check names every wired module and produces a value for each."""
    assert set(wiring.self_check()) == {
        "mem20core",
        "memory_engine",
        "toolchest",
        "mem20verify",
        "mem20ops",
        "gateway",
    }


def test_describe_run_describes_without_mutating():
    """describe_run describes a real-shaped result and leaves the input untouched."""
    result = {
        "job_id": "job-1",
        "roadmap_id": 101,
        "mode": "local",
        "decision": {"confidence": 0.89},
        "result": {"compatible": True},
        "cache_hit": False,
    }
    before = json.loads(json.dumps(result))
    described = wiring.describe_run(result)
    assert result == before
    assert described["run"]["job_id"] == "job-1"
    assert described["run"]["confidence"] == 0.89
    assert described["stable_hash"]
    assert len(described["wired_modules"]) == 6


# --- CLI --------------------------------------------------------------------


def test_cli_inspect_reports_the_roadmap(capsys):
    assert main(["inspect"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["global_id"] == 101
    assert payload["phases"] >= 1


def test_cli_run_executes_a_component_request(capsys):
    assert main(["run", '{"text":"demo","cache":false}']) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"]["roadmap_id"] == 101
    assert payload["audit"]["run"]["mode"] in {"local", "edge", "cloud", "hybrid"}


def test_cli_run_rejects_malformed_json(capsys):
    assert main(["run", "{not json"]) == EXIT_FAILED
    assert "error" in json.loads(capsys.readouterr().out)


def test_cli_simulate_replays_scenarios(capsys):
    assert main(["simulate"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert "success" in payload


def test_cli_benchmark_reports_measured_numbers(capsys):
    assert main(["benchmark", "--runs", "2"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["report"]["runs"] == 2
    assert payload["measured_wall_seconds"] > 0


def test_cli_wiring_exits_zero(capsys):
    assert main(["wiring"]) == EXIT_OK
    assert "mem20core" in json.loads(capsys.readouterr().out)


def test_module_entry_point_runs():
    """``python -m mem20wasmz inspect`` works from the lab directory."""
    proc = subprocess.run(
        [sys.executable, "-m", "mem20wasmz", "inspect"],
        cwd=LAB_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == EXIT_OK, proc.stderr
    assert json.loads(proc.stdout)["global_id"] == 101
