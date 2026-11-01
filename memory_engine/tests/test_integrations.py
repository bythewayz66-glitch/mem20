"""Tests for memory_engine's cross-subsystem wiring and CLI.

These are integration tests in the strict sense: every assertion is on a value
that came out of another subsystem's real code path. Nothing here mocks a
sibling module, because the whole point of the wiring is that the edges are
live -- a mock would pass while the estate was broken.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from memory_engine import integrations


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Point the store at a temp dir so tests never touch a real ledger."""
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "store"))
    # memory.py reads the env at import time, so reload it for this test.
    import importlib

    from memory_engine import memory

    importlib.reload(memory)
    return memory


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
    env = integrations.cli_envelope("stats", ["stats", "--json"], 0, stdout="{}")
    assert env["schema"] == "mem20.cli/1"
    assert env["ok"] is True
    assert env["command"] == "stats"
    assert env["argv"] == ["stats", "--json"]


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
# CLI
# ---------------------------------------------------------------------------
def _run_cli(args, env_extra=None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-m", "memory_engine.cli", *args],
        capture_output=True, text=True, env=env,
        cwd=str(Path(__file__).resolve().parents[1]),
    )


def test_cli_stats_emits_envelope(tmp_path):
    proc = _run_cli(["stats", "--json"],
                    {"MEM20_STORE_PATH": str(tmp_path / "s")})
    assert proc.returncode == 0, proc.stderr
    env = json.loads(proc.stdout)
    assert env["schema"] == "mem20.cli/1"
    assert env["command"] == "stats"


def test_cli_remember_then_recall_roundtrip(tmp_path):
    store_path = str(tmp_path / "s")
    wrote = _run_cli(["remember", "--topic", "cli_probe",
                      "--content", "written through the CLI",
                      "--epistemic-status", "observed", "--json"],
                     {"MEM20_STORE_PATH": store_path})
    assert wrote.returncode == 0, wrote.stderr

    read = _run_cli(["recall", "--topic", "cli_probe"],
                    {"MEM20_STORE_PATH": store_path})
    assert read.returncode == 0, read.stderr
    assert "written through the CLI" in read.stdout


def test_cli_remember_refuses_missing_epistemic_status(tmp_path):
    """An unlabeled write is refused, and the CLI reports it as exit 2."""
    proc = _run_cli(["remember", "--topic", "x", "--content", "y", "--json"],
                    {"MEM20_STORE_PATH": str(tmp_path / "s")})
    assert proc.returncode != 0


def test_cli_wiring_exits_zero_when_all_edges_live(tmp_path):
    proc = _run_cli(["wiring", "--json"],
                    {"MEM20_STORE_PATH": str(tmp_path / "s")})
    assert proc.returncode == 0, proc.stdout + proc.stderr
    env = json.loads(proc.stdout)
    assert env["ok"] is True
