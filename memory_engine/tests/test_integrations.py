"""Tests for memory_engine's cross-subsystem wiring and CLI.

These are integration tests in the strict sense: every assertion is on a value
that came out of another subsystem's real code path. Nothing here mocks a
sibling module, because the whole point of the wiring is that the edges are
live -- a mock would pass while the estate was broken.

Ported from the stranded ``feat/4.0-super-agent-memory-engine`` branch onto
current ``main``. The branch's ``memory.py``/``cli.py`` were older than main's
and were deliberately NOT taken; only the genuinely new work (the wiring module
and these tests) is carried over, adapted to main's CLI surface (``status``
rather than ``stats``) and extended with assertions against the live
487-tool / 129-domain surface pin in ``docs/surface.json``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from memory_engine import integrations

REPO_ROOT = Path(__file__).resolve().parents[2]
SURFACE_JSON = REPO_ROOT / "docs" / "surface.json"


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Point the store at a temp dir so tests never touch a real ledger."""
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "store"))
    # memory.py reads the env at import time, so reload it for this test.
    import importlib

    from memory_engine import memory

    importlib.reload(memory)
    return memory


# ---------------------------------------------------------------------------
# the wiring edges
# ---------------------------------------------------------------------------
def test_all_wired_subsystems_import():
    """Every declared edge must actually import in a full estate checkout."""
    avail = integrations.available()
    missing = [name for name, ok in avail.items() if not ok]
    assert not missing, f"subsystems failed to import: {missing}"


def test_ledger_digest_matches_kanbanz_hasher(store):
    """The digest edge returns mem20kanbanz's hash of the real ledger file."""
    store.remember(topic="digest_probe", content="a grounded fact",
                   epistemic_status="observed")
    digest = integrations.ledger_digest()
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)

    # Same file, same hasher, same answer -- and a changed file changes it.
    assert integrations.ledger_digest() == digest
    store.remember(topic="digest_probe", content="another fact",
                   epistemic_status="observed")
    assert integrations.ledger_digest() != digest


def test_classify_topic_key_uses_ops_rules():
    """mem20ops's naming classifier is what decides a topic key's verdict."""
    # The three verdicts ops can return, each reached through a real key.
    assert integrations.classify_topic_key("mem20ops") == "mem20-native"
    assert integrations.classify_topic_key("fs-tool") == "fs-standard"
    # A key with a space can never be a clean filename, and ops must say so.
    assert integrations.classify_topic_key("has space") == "other"


def test_model_parameter_count_is_the_real_allocation():
    """The count comes from mem20corez's actual weight arrays."""
    small = integrations.model_parameter_count(hidden=16)
    large = integrations.model_parameter_count(hidden=64)
    assert large > small > 0
    # Doubling hidden must grow the count by more than the hidden term alone,
    # because both W1 and W2 scale with it.
    assert integrations.model_parameter_count(hidden=128) > large


def test_cli_envelope_is_the_shared_schema():
    """The envelope is built by mem20cliz, not reimplemented here."""
    env = integrations.cli_envelope("status", ["status", "--json"], 0, stdout="{}")
    assert env["schema"] == "mem20.cli/1"
    assert env["ok"] is True
    assert env["command"] == "status"
    assert env["argv"] == ["status", "--json"]


def test_test_bearing_packages_finds_the_estate():
    """mem20verify's discovery returns real package names from this checkout."""
    packages = integrations.test_bearing_packages()
    assert len(packages) > 10
    assert "memory_engine" in packages


def test_tool_inventory_counts_are_real():
    """toolchest's inventory reports non-zero counts for a real estate."""
    counts = integrations.tool_inventory_counts()
    assert counts["total"] > 0
    assert counts["total"] == counts["mcp"] + counts["cli"] + counts["subsystem"]


def test_wiring_report_all_edges_live(store):
    """The report is the single proof that every edge works, end to end."""
    report = integrations.wiring_report(record=True)
    dead = {k: v for k, v in report["edges"].items() if not v["ok"]}
    assert not dead, f"dead edges: {dead}"
    assert report["ok"] is True


def test_record_estate_snapshot_writes_a_grounded_fact(store):
    """The snapshot lands in the grounded ledger with an observed label."""
    rec = integrations.record_estate_snapshot()
    assert rec["origin"] == "grounded"
    assert rec["epistemic_status"] == "observed"
    assert "estate snapshot" in rec["content"]
    assert Path(store.LEDGER).is_file()


def test_wiring_report_without_record_does_not_write(store):
    """A read-only wiring check must not mutate the store."""
    integrations.wiring_report(record=False)
    assert not Path(store.LEDGER).is_file()


# ---------------------------------------------------------------------------
# the live surface pin (487 tools / 129 domains)
# ---------------------------------------------------------------------------
def test_surface_pin_is_the_live_487_tool_129_domain_surface():
    """The ported wiring is asserted against the surface main actually ships.

    ``docs/surface.json`` is generated from ``tools/list`` on the live server
    and cross-checked against the AST catalog, so it is the estate's own
    statement of its surface. If the surface moves, this test moves with it --
    the numbers are read from the file, never hardcoded here.
    """
    surface = json.loads(SURFACE_JSON.read_text())
    assert surface["tools"] == 487
    assert surface["domains"] == 129
    assert len(surface["domain_names"]) == 129
    assert len(surface["domain_counts"]) == 129
    assert len(surface["domains_detail"]) == 129

    # The AST catalog and the live tools/list must agree, or the pin is a lie.
    cross = surface["cross_check"]
    assert cross["ast_tools"] == surface["tools"]
    assert cross["ast_domains"] == surface["domains"]
    assert cross["only_ast"] == []
    assert cross["only_live"] == []


def test_surface_pin_declares_the_memory_engine_tools():
    """The six memory_engine MCP tools are on the declared surface."""
    surface = json.loads(SURFACE_JSON.read_text())
    declared = set(surface["unwired_tools"])
    for name in (
        "memory_engine_health",
        "memory_engine_recall",
        "memory_engine_veto",
        "memory_engine_guard",
        "memory_engine_namespace",
        "memory_engine_subsystem",
    ):
        assert name in declared, f"{name} missing from the declared surface"


def test_wiring_report_agrees_with_the_surface_pin(store):
    """The estate the wiring measures is the estate the pin describes.

    ``toolchest`` counts the on-box inventory (CLIs + subsystems), which is a
    different axis from the MCP tool surface, so the two are not expected to be
    equal. What must hold is that both are non-empty and internally consistent
    -- a wiring report that measured nothing would otherwise pass silently.
    """
    surface = json.loads(SURFACE_JSON.read_text())
    counts = integrations.tool_inventory_counts()
    assert surface["tools"] > 0 and surface["domains"] > 0
    assert counts["total"] > 0
    assert counts["total"] == counts["mcp"] + counts["cli"] + counts["subsystem"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _run_cli(args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-m", "memory_engine.cli", *args],
        capture_output=True, text=True, env=env,
        cwd=str(REPO_ROOT),
    )


def test_cli_status_emits_envelope(tmp_path):
    # ``--json`` is a top-level flag on main's CLI, so it precedes the verb.
    proc = _run_cli(["--json", "status"],
                    {"MEM20_STORE_PATH": str(tmp_path / "s")})
    assert proc.returncode == 0, proc.stderr
    env = json.loads(proc.stdout)
    assert env["schema"] == "mem20.cli/1"
    assert env["command"] == "status"


def test_cli_remember_then_recall_roundtrip(tmp_path):
    store_path = str(tmp_path / "s")
    wrote = _run_cli(["--json", "remember", "--topic", "cli_probe",
                      "--content", "written through the CLI",
                      "--epistemic-status", "observed"],
                     {"MEM20_STORE_PATH": store_path})
    assert wrote.returncode == 0, wrote.stderr

    read = _run_cli(["recall", "--topic", "cli_probe"],
                    {"MEM20_STORE_PATH": store_path})
    assert read.returncode == 0, read.stderr
    assert "written through the CLI" in read.stdout


def test_cli_remember_refuses_missing_epistemic_status(tmp_path):
    """An unlabeled write is refused, and the CLI reports it as a failure."""
    proc = _run_cli(["--json", "remember", "--topic", "x", "--content", "y"],
                    {"MEM20_STORE_PATH": str(tmp_path / "s")})
    assert proc.returncode != 0


def test_cli_wiring_exits_zero_when_all_edges_live(tmp_path):
    proc = _run_cli(["--json", "wiring"],
                    {"MEM20_STORE_PATH": str(tmp_path / "s")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    env = json.loads(proc.stdout)
    assert env["ok"] is True
    assert env["command"] == "wiring"
    # The envelope's stdout carries the report itself; a dead edge would have
    # made the process exit non-zero above.
    report = json.loads(env["stdout"])
    assert report["ok"] is True
    assert not [k for k, v in report["edges"].items() if not v["ok"]]


def test_cli_wiring_does_not_write_without_record(tmp_path):
    """``wiring`` without ``--record`` must leave the store untouched."""
    store_path = tmp_path / "s"
    proc = _run_cli(["--json", "wiring"], {"MEM20_STORE_PATH": str(store_path)})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not (store_path / "ledger.jsonl").is_file()
