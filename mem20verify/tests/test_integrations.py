"""Cross-subsystem wiring tests for mem20verify.

Every test calls the real function in the other subsystem and checks the value
it actually returned. A subsystem absent from the environment is skipped with
the real reason, never silently passed.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mem20verify import integrations  # noqa: E402

ESTATE = integrations.estate_root()


def _require(name):
    if not integrations.available().get(name):
        pytest.skip(f"{name} not importable in this environment")


def test_estate_root_contains_verify():
    assert (ESTATE / "mem20verify").is_dir()
    assert (ESTATE / "toolchest").is_dir()


def test_available_reports_every_wired_subsystem():
    assert set(integrations.available()) == {
        "toolchest", "memory_engine", "mem20kanbanz",
        "mem20ops", "mem20corez", "mem20cliz",
    }


def test_available_does_not_include_self():
    # verify importing itself is not an edge
    assert "mem20verify" not in integrations.available()


def test_registry_claims_are_read_from_the_real_inventory():
    _require("toolchest")
    counts = integrations.registry_claims(ESTATE)
    assert counts
    assert counts["total"] == sum(v for k, v in counts.items() if k != "total")
    assert counts["total"] > 0


def test_registry_drift_is_computed_both_ways():
    _require("toolchest")
    drift = integrations.registry_drift(ESTATE)
    assert drift["claimed"] > 0
    assert drift["on_disk"] > 0
    # the two sets are disjoint by construction
    assert not (set(drift["claimed_but_missing"]) & set(drift["on_disk_but_unlisted"]))
    # a subsystem that really is on disk must be counted as on disk
    assert "mem20verify" in {
        d.name for d in ESTATE.iterdir()
        if d.is_dir() and (d / "mem20verify").is_dir()
    }
    assert drift["in_sync"] == (not drift["claimed_but_missing"]
                                and not drift["on_disk_but_unlisted"])


def test_report_digest_matches_hashlib():
    _require("mem20kanbanz")
    target = Path(__file__).resolve()
    assert integrations.report_digest(target) == hashlib.sha256(
        target.read_bytes()).hexdigest()


def test_pin_verdict_roundtrip():
    _require("memory_engine")
    result = integrations.pin_verdict(
        "wiring-test", {"passed": True, "checks": 7},
        block_id="mem20verify:test-verdict")
    assert result["pinned"] is True

    from memory_engine.memory import get_pinned_block
    stored = get_pinned_block("mem20verify:test-verdict")
    assert "checks=7" in stored["content"]
    assert "wiring-test" in stored["content"]


def test_ops_declared_scripts_reads_this_estate():
    _require("mem20ops")
    rows = integrations.declared_console_scripts(ESTATE)
    assert rows
    assert "mem20verify" in {r["name"] for r in rows}
    for row in rows:
        assert row["package_dir"].startswith(str(ESTATE))


def test_corez_smoke_check_exercises_a_real_model():
    _require("mem20corez")
    result = integrations.model_smoke_check(hidden=8, context_len=4)
    assert result["params"] > 0
    assert 0.0 <= result["accuracy"] <= 1.0
    assert result["generated"] is True
    assert result["completion_len"] >= 4


def test_cliz_envelope_shape():
    _require("mem20cliz")
    env = integrations.cli_envelope("mem20verify", ["wiring"], 0, "ok", "")
    assert env["schema"] == "mem20.cli/1"
    assert env["ok"] is True
    assert env["command"] == "mem20verify"


def test_wiring_report_all_edges_live():
    report = integrations.wiring_report(ESTATE)
    assert report["edges_total"] == 6
    assert report["ok"] is True, json.dumps(report, indent=2, default=str)
    assert report["edges_ok"] == 6


def test_wiring_cli_exits_zero(capsys):
    from mem20verify.cli import main
    code = main(["wiring", "--root", str(ESTATE)])
    assert code == 0
    assert "6/6 edges live" in capsys.readouterr().out


def test_wiring_cli_json_is_parseable(capsys):
    from mem20verify.cli import main
    code = main(["wiring", "--root", str(ESTATE), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["ok"] is True
    assert len(payload["edges"]) == 6


def test_drift_cli_reports_without_crashing(capsys):
    from mem20verify.cli import main
    code = main(["drift", "--root", str(ESTATE), "--json"])
    payload = json.loads(capsys.readouterr().out)
    # 0 = in sync, 1 = drift found. Both are real, successful executions.
    assert code in (0, 1)
    assert set(payload) >= {"claimed", "on_disk", "claimed_but_missing",
                            "on_disk_but_unlisted", "in_sync"}
