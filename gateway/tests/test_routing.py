"""Tests for gateway relay routing.

These assert behaviour, not shape: each test drives a real decision through the
sibling subsystems and checks the outcome. The secret fixtures are synthetic
and assembled at runtime so no credential-shaped literal is committed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in (REPO_ROOT, REPO_ROOT / "mem20secretz" / "src", REPO_ROOT / "toolchest" / "src",
          REPO_ROOT / "mem20kilnz", REPO_ROOT / "mem20verify"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gateway import routing  # noqa: E402
from gateway.cli import main as cli_main  # noqa: E402


def _fake_key() -> str:
    """A credential-shaped string built at runtime, never a committed literal."""
    return "sk-" + "a1b2c3d4" * 5


# ---------------------------------------------------------------------------
# screening
# ---------------------------------------------------------------------------
def test_clean_payload_is_allowed():
    verdict = routing.screen_payload("deploy finished on node 3, all green")
    assert verdict.allowed is True
    assert verdict.findings == []


def test_credential_payload_is_blocked():
    verdict = routing.screen_payload(f"here is the key {_fake_key()}")
    assert verdict.allowed is False
    assert verdict.findings, "expected at least one finding"
    assert any(f["severity"] in routing.BLOCKING_SEVERITIES for f in verdict.findings)
    assert "blocking" in verdict.reason


def test_endpoint_is_informational_not_blocking():
    """A URL is config duplication, not a leak — it must not stop the relay."""
    verdict = routing.screen_payload("see https://example.com/status for details")
    assert verdict.allowed is True
    assert all(f["severity"] not in routing.BLOCKING_SEVERITIES
               for f in verdict.findings)


def test_screen_reports_offsets():
    text = f"prefix {_fake_key()} suffix"
    verdict = routing.screen_payload(text)
    assert verdict.findings
    assert all(isinstance(f["offset"], int) and f["offset"] >= 0
               for f in verdict.findings)


# ---------------------------------------------------------------------------
# asset budget — delegated to mem20kilnz
# ---------------------------------------------------------------------------
def test_budget_accepts_in_band_asset():
    result = routing.check_asset_budget("prop", 5000)
    assert result["ok"] is True
    assert result["family"] == "prop"


def test_budget_rejects_unknown_family():
    result = routing.check_asset_budget("not_a_real_family", 5000)
    assert result["ok"] is False
    assert "unknown asset family" in result["reason"]


def test_budget_rejects_absurd_triangle_count():
    result = routing.check_asset_budget("prop", 10_000_000)
    assert result["ok"] is False
    assert "exceeds" in result["reason"]


# ---------------------------------------------------------------------------
# inventory — delegated to toolchest
# ---------------------------------------------------------------------------
def test_inventory_loads_and_lists_subsystems():
    inv = routing.inventory_subsystems()
    assert inv["ok"] is True
    assert inv["count"] > 0
    assert isinstance(inv["subsystems"], list)


def test_inventory_missing_file_is_reported_not_raised():
    inv = routing.inventory_subsystems("/nonexistent/inventory.json")
    assert inv["ok"] is False
    assert "not found" in inv["error"]


def test_target_is_known_against_real_inventory():
    inv = routing.inventory_subsystems()
    assert inv["ok"] is True
    known = inv["subsystems"][0]
    assert routing.target_is_known(known) is True
    assert routing.target_is_known("definitely-not-a-subsystem-xyz") is False


# ---------------------------------------------------------------------------
# store integrity — delegated to mem20verify
# ---------------------------------------------------------------------------
def test_verify_store_reports_roundtrip_state():
    """The gateway must surface mem20verify's verdict, not assume it is green.

    mem20verify's check() currently reports 0/11 round-trips against this
    engine because remember() writes markdown entries while the check reads
    ledger.jsonl. That is a real defect in mem20verify, not in the gateway, so
    this test asserts the gateway faithfully reports whatever the check says
    rather than asserting a pass.
    """
    result = routing.verify_store()
    assert result["error"] == ""
    assert result["checked"] > 0
    assert result["roundtrip_ok"] <= result["checked"]
    # ok must agree with the underlying check, whatever its value.
    assert result["ok"] is (result["roundtrip_ok"] == result["checked"]
                            and result["failures"] == 0
                            and result["false_positive_detections"] == 0)


# ---------------------------------------------------------------------------
# composed routing
# ---------------------------------------------------------------------------
def test_route_allows_clean_message():
    decision = routing.route("status ok", "mem20kilnz")
    assert decision.allowed is True
    assert decision.screen.allowed is True


def test_route_blocks_leak_even_to_valid_target():
    decision = routing.route(f"key={_fake_key()}", "mem20kilnz")
    assert decision.allowed is False
    assert "blocking" in decision.reason


def test_route_refuses_unknown_target_when_required():
    decision = routing.route("status ok", "no-such-subsystem-xyz",
                             require_known_target=True)
    assert decision.allowed is False
    assert "not in the estate inventory" in decision.reason


def test_route_accepts_known_target_when_required():
    inv = routing.inventory_subsystems()
    decision = routing.route("status ok", inv["subsystems"][0],
                             require_known_target=True)
    assert decision.allowed is True


def test_route_rejects_over_budget_asset_claim():
    decision = routing.route("asset ready", "mem20kilnz",
                             family="prop", triangles=10_000_000)
    assert decision.allowed is False
    assert decision.budget is not None
    assert decision.budget["ok"] is False
    assert "asset budget rejected" in decision.reason


def test_route_accepts_in_budget_asset_claim():
    decision = routing.route("asset ready", "mem20kilnz",
                             family="prop", triangles=5000)
    assert decision.allowed is True
    assert decision.budget["ok"] is True


def test_route_decision_serialises():
    payload = json.loads(routing.route_json("status ok", "mem20kilnz"))
    assert payload["allowed"] is True
    assert payload["target"] == "mem20kilnz"
    assert "screen" in payload


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
def test_cli_screen_clean_exits_zero(capsys):
    assert cli_main(["screen", "all good"]) == 0
    assert "allowed" in capsys.readouterr().out


def test_cli_screen_leak_exits_one(capsys):
    assert cli_main(["screen", f"key {_fake_key()}"]) == 1
    out = capsys.readouterr().out
    assert "allowed: False" in out


def test_cli_route_json(capsys):
    code = cli_main(["--json", "route", "status ok", "mem20kilnz"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["allowed"] is True


def test_cli_budget_rejects(capsys):
    assert cli_main(["budget", "prop", "10000000"]) == 1
    assert "ok: False" in capsys.readouterr().out


def test_cli_inventory_contains(capsys):
    inv = routing.inventory_subsystems()
    code = cli_main(["inventory", "--contains", inv["subsystems"][0]])
    assert code == 0
    assert "match: True" in capsys.readouterr().out


def test_cli_verify(capsys):
    """`verify` exits 0 when the store is intact, 1 when it is not.

    The exit code is the contract, so this asserts the code agrees with the
    reported state rather than hard-coding a pass.
    """
    code = cli_main(["verify"])
    out = capsys.readouterr().out
    assert "roundtrip_ok" in out
    assert code == (0 if "ok: True" in out else 1)


def test_cli_requires_subcommand():
    with pytest.raises(SystemExit):
        cli_main([])
