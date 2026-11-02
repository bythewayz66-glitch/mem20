"""The loader audit must actually run, and must actually catch drift.

These tests exist because ``mem20_mcp`` is a forwarding package, and the failure
mode of a forwarding package is silent: a shim that stops forwarding and starts
containing code still imports, still exposes the right names, and still passes a
smoke test. The original bug here was exactly that shape -- a stale
``tools/world_tools.py`` that had lost ``WorldToolsMixin``, so ``server.py``
raised ``ImportError`` at boot.

Each test drives ``run_audit`` -- the same entry point the CLI uses -- and
asserts on what the estate modules decided, not on a mock of them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from mem20_mcp import loader_audit
from mem20_mcp.loader_audit import AuditRefused, audit_shim, run_audit


# ---------------------------------------------------------------------------
# The wiring itself: six estate modules, imported and called.
# ---------------------------------------------------------------------------


def test_loader_audit_imports_six_estate_modules():
    """Criterion 6 is a claim about real imports; assert the names resolve."""
    from mem20liez.gates import check_prohibited_uses
    from mem20ops.clicheck import classify_naming
    from mem20verify.linters import noop_bodies
    from mem20ircz.filter import NoiseMeter, classify
    from mem20temporaldatabasefabricz.temporal.interval import contains
    from mem20dreamz import ledger

    assert loader_audit.check_prohibited_uses is check_prohibited_uses
    assert loader_audit.classify_naming is classify_naming
    assert loader_audit.noop_bodies is noop_bodies
    assert loader_audit.classify_wire_line is classify
    assert loader_audit.NoiseMeter is NoiseMeter
    assert loader_audit.interval_contains is contains
    assert loader_audit.dreamz_ledger is ledger


# ---------------------------------------------------------------------------
# The real package is clean.
# ---------------------------------------------------------------------------


def test_real_package_audits_clean():
    audit = run_audit(record=False)
    assert audit.shims, "no shims discovered; the audit would pass vacuously"
    assert audit.clean, [s.as_dict() for s in audit.broken]


def test_every_shim_forwards():
    audit = run_audit(record=False)
    for shim in audit.shims:
        assert shim.forwards, f"{shim.module} does not call _load()"
        assert shim.stub_issues == 0, f"{shim.module} has stub bodies"


def test_loader_machinery_is_not_audited_as_a_shim():
    audit = run_audit(record=False)
    names = {s.module for s in audit.shims}
    assert "_forward" not in names
    assert "loader_audit" not in names
    assert "cli" not in names


# ---------------------------------------------------------------------------
# Naming: mem20ops.clicheck.classify_naming
# ---------------------------------------------------------------------------


def test_mem20_native_package_name_is_admitted():
    assert loader_audit.check_package_name("mem20_mcp") == "mem20-native"


def test_foreign_package_name_is_refused_by_clicheck():
    with pytest.raises(AuditRefused) as exc:
        loader_audit.check_package_name("helper")
    assert exc.value.check == "naming"
    assert "other" in exc.value.reason


def test_run_audit_refuses_a_foreign_package_name():
    with pytest.raises(AuditRefused):
        run_audit(record=False, package="helper")


# ---------------------------------------------------------------------------
# Forwarding: the drift detector
# ---------------------------------------------------------------------------


def test_shim_that_does_not_forward_is_caught(tmp_path):
    """The exact silent-drift failure: code instead of forwarding."""
    (tmp_path / "mem20_mcp_drift.py").write_text(
        "def do_the_thing():\n    return 42\n"
    )
    report = audit_shim(tmp_path / "mem20_mcp_drift.py")
    assert report.forwards is False
    assert report.ok is False
    assert any("reaches neither" in p for p in report.problems)


def test_shim_that_forwards_is_accepted(tmp_path):
    (tmp_path / "mem20_mcp_good.py").write_text(
        "from mem20_mcp._forward import load as _load\n"
        "_impl = _load('health.py', 'health')\n"
    )
    report = audit_shim(tmp_path / "mem20_mcp_good.py")
    assert report.forwards is True
    assert report.ok is True


# ---------------------------------------------------------------------------
# Stub bodies: mem20verify.linters.noop_bodies
# ---------------------------------------------------------------------------


def test_stub_body_is_refused_by_linter(tmp_path):
    (tmp_path / "mem20_mcp_stub.py").write_text(
        "from mem20_mcp._forward import load as _load\n"
        "_impl = _load('x.py', 'x')\n"
        "def forward():\n    pass\n"
    )
    report = audit_shim(tmp_path / "mem20_mcp_stub.py")
    assert report.stub_issues >= 1
    assert report.ok is False


def test_unparseable_shim_is_reported(tmp_path):
    (tmp_path / "mem20_mcp_bad.py").write_text("def broken(:\n")
    report = audit_shim(tmp_path / "mem20_mcp_bad.py")
    assert report.ok is False
    assert any("does not parse" in p for p in report.problems)


# ---------------------------------------------------------------------------
# Prohibited uses: mem20liez.gates.check_prohibited_uses
# ---------------------------------------------------------------------------


def test_permitted_use_passes():
    assert loader_audit.check_intended_uses(["loader_integrity"]) == ("loader_integrity",)


def test_no_declared_uses_passes():
    assert loader_audit.check_intended_uses(None) == ()


def test_prohibited_use_is_refused_by_gate():
    with pytest.raises(AuditRefused) as exc:
        loader_audit.check_intended_uses(["automated_detention"])
    assert exc.value.check == "prohibited_use"


def test_prohibited_use_normalises_spacing_and_case():
    with pytest.raises(AuditRefused):
        loader_audit.check_intended_uses(["  Automated Detention  "])


def test_run_audit_refuses_a_prohibited_use():
    with pytest.raises(AuditRefused):
        run_audit(record=False, intended_uses=["clinical_diagnosis"])


# ---------------------------------------------------------------------------
# Audit window: mem20temporaldatabasefabricz.temporal.interval.contains
# ---------------------------------------------------------------------------


def test_instant_inside_window_passes():
    assert loader_audit.check_audit_window(
        "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2026-06-01T00:00:00Z"
    ) is True


def test_instant_after_window_is_refused():
    with pytest.raises(AuditRefused) as exc:
        loader_audit.check_audit_window(
            "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2027-06-01T00:00:00Z"
        )
    assert exc.value.check == "outside_window"


def test_open_ended_window_passes():
    assert loader_audit.check_audit_window(None, None, "2030-01-01T00:00:00Z") is True


# ---------------------------------------------------------------------------
# Wire filter: mem20ircz.filter.classify + NoiseMeter
# ---------------------------------------------------------------------------


def test_human_channel_message_carries_signal():
    kept, meter = loader_audit.filter_wire(
        [{"command": "PRIVMSG", "text": "server booted", "prefix": "ana!u@h",
          "params": ("#ops",)}]
    )
    assert len(kept) == 1
    assert meter.kept == 1


def test_motd_numeric_is_noise():
    kept, meter = loader_audit.filter_wire([{"command": "372", "text": "- motd"}])
    assert kept == []
    assert meter.by_reason["numeric.motd"] == 1


def test_mixed_lines_keep_only_the_signal():
    kept, meter = loader_audit.filter_wire([
        {"command": "001", "text": "welcome"},
        {"command": "PRIVMSG", "text": "server booted", "prefix": "ana!u@h",
         "params": ("#ops",)},
        {"command": "JOIN", "params": ("#ops",)},
    ])
    assert [line.text for line in kept] == ["server booted"]
    assert meter.seen == 3 and meter.swallowed == 2
    assert 0.0 < meter.waste_ratio < 1.0


def test_run_audit_reports_wire_savings():
    audit = run_audit(
        record=False,
        wire_lines=[
            {"command": "372", "text": "- motd"},
            {"command": "PRIVMSG", "text": "server booted", "prefix": "ana!u@h",
             "params": ("#ops",)},
        ],
    )
    assert audit.wire_kept == 1
    assert audit.wire_swallowed == 1
    assert audit.wire_reasons == {"numeric.motd": 1}


# ---------------------------------------------------------------------------
# Provenance: mem20dreamz.ledger.commit_raw
# ---------------------------------------------------------------------------


def test_provenance_reports_durability_honestly():
    audit = run_audit(record=True)
    prov = audit.provenance
    assert "committed" in prov
    if prov["committed"]:
        assert prov.get("cid")
    else:
        assert prov.get("reason")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_audit_exits_zero_on_clean_package(capsys):
    from mem20_mcp.cli import main

    assert main(["audit"]) == 0
    out = capsys.readouterr().out
    assert "CLEAN" in out


def test_cli_audit_json_is_parseable(capsys):
    import json

    from mem20_mcp.cli import main

    assert main(["audit", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is True
    assert payload["shims"]


def test_cli_refuses_a_prohibited_use(capsys):
    from mem20_mcp.cli import main

    assert main(["audit", "--intended-use", "automated_detention"]) == 2
    assert "refused" in capsys.readouterr().out
