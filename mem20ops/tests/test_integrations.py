"""Cross-subsystem wiring tests for mem20ops.

Every test calls the real function in the other subsystem and checks the value
it actually returned. A subsystem absent from the environment is skipped with
the real reason, never silently passed.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from mem20ops import integrations  # noqa: E402

ESTATE = integrations.estate_root()


def _require(name):
    if not integrations.available().get(name):
        pytest.skip(f"{name} not importable in this environment")


def test_estate_root_contains_ops():
    assert (ESTATE / "mem20ops").is_dir()
    assert (ESTATE / "toolchest").is_dir()


def test_available_reports_every_wired_subsystem():
    assert set(integrations.available()) == {
        "toolchest", "memory_engine", "mem20kanbanz",
        "mem20corez", "mem20cliz", "mem20verify",
    }


def test_import_does_not_leave_estate_paths_on_sys_path():
    # Importing this module must not change the meaning of another test's
    # environment probe, so the bootstrap is undone once the imports bind.
    for added in integrations._ADDED_PATHS:
        assert added not in sys.path


def test_registry_summary_reads_the_real_inventory():
    _require("toolchest")
    summary = integrations.registry_summary(ESTATE)
    assert summary["entries"] > 0
    assert summary["generated_at"]
    assert summary["counts"]["total"] == summary["entries"]


def test_pin_ops_snapshot_roundtrip():
    _require("memory_engine")
    result = integrations.pin_ops_snapshot(
        {"healthy": True, "units": 12}, block_id="mem20ops:test-snapshot")
    assert result["pinned"] is True

    from memory_engine.memory import get_pinned_block
    stored = get_pinned_block("mem20ops:test-snapshot")
    assert "units=12" in stored["content"]
    assert "healthy=True" in stored["content"]


def test_pin_ops_snapshot_replaces_previous_reading():
    _require("memory_engine")
    integrations.pin_ops_snapshot({"units": 1}, block_id="mem20ops:test-repin")
    integrations.pin_ops_snapshot({"units": 2}, block_id="mem20ops:test-repin")

    from memory_engine.memory import get_pinned_block
    assert "units=2" in get_pinned_block("mem20ops:test-repin")["content"]


def test_report_digest_matches_hashlib():
    _require("mem20kanbanz")
    target = Path(__file__).resolve()
    assert integrations.report_digest(target) == hashlib.sha256(
        target.read_bytes()).hexdigest()


def test_model_health_exercises_a_real_model():
    _require("mem20corez")
    health = integrations.model_health(hidden=8, context_len=4)
    assert health["params"] > 0
    assert 0.0 <= health["accuracy"] <= 1.0
    assert health["generated"] is True
    assert health["completion_len"] >= 4


def test_cliz_envelope_shape():
    _require("mem20cliz")
    env = integrations.cli_envelope("mem20ops", ["wiring"], 0, "ok", "")
    assert env["schema"] == "mem20.cli/1"
    assert env["ok"] is True
    assert env["command"] == "mem20ops"


def test_verify_discovers_test_bearing_packages():
    _require("mem20verify")
    packages = integrations.test_bearing_packages(ESTATE)
    assert "mem20ops" in packages
    assert "mem20verify" in packages


def test_wiring_report_all_edges_live():
    report = integrations.wiring_report(ESTATE)
    assert report["edges_total"] == 6
    assert report["ok"] is True, json.dumps(report, indent=2, default=str)
    assert report["edges_ok"] == 6


def test_wiring_cli_exits_zero(capsys):
    from mem20ops.cli import main
    code = main(["wiring", "--root", str(ESTATE)])
    assert code == 0
    assert "6/6 edges live" in capsys.readouterr().out


def test_wiring_cli_json_is_parseable(capsys):
    from mem20ops.cli import main
    # ``--json`` is a global flag on this CLI, so it precedes the subcommand.
    code = main(["--json", "wiring", "--root", str(ESTATE)])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert len(payload["edges"]) == 6
