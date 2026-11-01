"""Cross-subsystem wiring tests for toolchest.

These are not import-only assertions: every test calls the real function in the
other subsystem and checks the value it actually returned. A subsystem that is
absent from the environment is skipped with the real reason, never silently
passed.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from toolchest import integrations  # noqa: E402

ESTATE = integrations.estate_root()


def _require(name):
    if not integrations.available().get(name):
        pytest.skip(f"{name} not importable in this environment")


def test_estate_root_contains_toolchest():
    assert (ESTATE / "toolchest").is_dir()
    assert (ESTATE / "memory_engine").is_dir()


def test_available_reports_every_wired_subsystem():
    avail = integrations.available()
    assert set(avail) == {
        "memory_engine", "mem20kanbanz", "mem20ops",
        "mem20corez", "mem20cliz", "mem20verify",
    }


def test_memory_engine_pin_block_roundtrip():
    _require("memory_engine")
    result = integrations.pin_inventory_snapshot(
        {"counts": {"mcp": 1, "cli": 2, "subsystem": 3, "total": 6},
         "generated_at": "2026-11-01T00:00:00Z"},
        block_id="toolchest:test-inventory",
    )
    assert result["pinned"] is True
    assert result["block_id"] == "toolchest:test-inventory"

    # the block is really readable back out of the engine
    from memory_engine.memory import get_pinned_block
    stored = get_pinned_block("toolchest:test-inventory")
    assert "total=6" in stored["content"]


def test_memory_engine_repin_replaces_previous_snapshot():
    _require("memory_engine")
    first = integrations.pin_inventory_snapshot(
        {"counts": {"total": 1}, "generated_at": "t1"}, block_id="toolchest:test-repin")
    second = integrations.pin_inventory_snapshot(
        {"counts": {"total": 2}, "generated_at": "t2"}, block_id="toolchest:test-repin")
    assert first["pinned"] and second["pinned"]

    from memory_engine.memory import get_pinned_block
    assert "total=2" in get_pinned_block("toolchest:test-repin")["content"]


def test_kanbanz_sha256_matches_hashlib():
    _require("mem20kanbanz")
    import hashlib
    target = Path(__file__).resolve()
    expected = hashlib.sha256(target.read_bytes()).hexdigest()
    assert integrations.inventory_digest(target) == expected


def test_ops_declared_scripts_reads_this_estate():
    _require("mem20ops")
    rows = integrations.declared_console_scripts(ESTATE)
    assert rows, "no console scripts declared anywhere in the estate"
    names = {r["name"] for r in rows}
    # mem20ops.clicheck scans the mem20* project directories, so the assertion
    # is on a real mem20* console script rather than on toolchest itself.
    assert "fs-ops" in names
    for row in rows:
        assert row["package_dir"].startswith(str(ESTATE))


def test_corez_parameter_count_is_real():
    _require("mem20corez")
    counts = integrations.model_parameter_counts(hidden=8, context_len=4)
    assert counts["params"] > 0
    assert counts["hidden"] == 8
    assert counts["context_len"] == 4
    # a wider hidden layer must have strictly more parameters
    wider = integrations.model_parameter_counts(hidden=16, context_len=4)
    assert wider["params"] > counts["params"]


def test_cliz_envelope_shape():
    _require("mem20cliz")
    env = integrations.cli_envelope("toolchest", ["wiring"], 0, "ok", "")
    assert env["schema"] == "mem20.cli/1"
    assert env["ok"] is True
    assert env["command"] == "toolchest"
    assert env["exit_code"] == 0


def test_verify_discovers_test_bearing_packages():
    _require("mem20verify")
    packages = integrations.test_bearing_packages(ESTATE)
    assert "toolchest" in packages
    assert "mem20verify" in packages


def test_wiring_report_all_edges_live():
    report = integrations.wiring_report(ESTATE)
    assert report["edges_total"] == 6
    assert report["ok"] is True, json.dumps(report, indent=2, default=str)
    assert report["edges_ok"] == 6


def test_wiring_cli_exits_zero(capsys):
    from toolchest.cli import main
    code = main(["wiring", "--root", str(ESTATE)])
    out = capsys.readouterr().out
    assert code == 0
    assert "6/6 edges live" in out


def test_wiring_cli_json_is_parseable(capsys):
    from toolchest.cli import main
    code = main(["wiring", "--root", str(ESTATE), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert len(payload["edges"]) == 6
