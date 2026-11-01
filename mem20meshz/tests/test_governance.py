"""Admission control must actually run on the dispatch path.

These tests exist because the six mesh engines were vendored from six separate
packages, and a policy that lived in one of them stops being enforced the moment
they share a dispatcher. Each test drives ``MasterEngine.execute`` -- the same
entry point the CLI and the MCP tool use -- and asserts on what the estate
modules decided, not on a mock of them.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from mem20meshz import governance
from mem20meshz.runtime import MasterEngine


@pytest.fixture(scope="module")
def engine():
    return MasterEngine()


# ---------------------------------------------------------------------------
# The wiring itself: six estate modules, imported and called.
# ---------------------------------------------------------------------------


def test_governance_imports_six_estate_modules():
    """Criterion 6 is a claim about real imports; assert the names resolve."""
    from mem20liez.gates import check_prohibited_uses
    from mem20ops.clicheck import classify_naming
    from mem20verify.linters import noop_bodies
    from mem20ircz.filter import NoiseMeter, classify
    from mem20temporaldatabasefabricz.temporal.interval import contains
    from mem20dreamz import ledger

    assert governance.check_prohibited_uses is check_prohibited_uses
    assert governance.classify_naming is classify_naming
    assert governance.noop_bodies is noop_bodies
    assert governance.classify_wire_line is classify
    assert governance.NoiseMeter is NoiseMeter
    assert governance.interval_contains is contains
    assert governance.dreamz_ledger is ledger


def test_execute_records_an_admission_for_every_mesh(engine):
    engine.execute({"text": "demo"})
    report = engine.admission_report()
    assert set(report) == set(engine.engines)
    for name, adm in report.items():
        assert adm["mesh"] == name
        assert adm["naming"] == "mem20-native"
        assert adm["stub_issues"] == 0
        assert adm["window_ok"] is True


def test_execute_records_provenance_for_every_mesh(engine):
    engine.execute({"text": "demo"})
    prov = engine.provenance_report()
    assert set(prov) == set(engine.engines)
    for record in prov.values():
        # braid is not reachable in a bare clone; the ledger must say so
        # rather than pretend the node was written.
        assert "committed" in record
        if not record["committed"]:
            assert record["reason"]


# ---------------------------------------------------------------------------
# Naming: mem20ops.clicheck.classify_naming
# ---------------------------------------------------------------------------


def test_mem20_native_tool_name_is_admitted():
    assert governance.check_tool_name("mem20meshz_crisis") == "mem20-native"


def test_fs_standard_tool_name_is_admitted():
    assert governance.check_tool_name("fs-mesh") == "fs-standard"


def test_foreign_tool_name_is_refused_by_clicheck():
    with pytest.raises(governance.MeshRefused) as exc:
        governance.check_tool_name("helper")
    assert exc.value.check == "naming"
    assert "other" in exc.value.reason


def test_execute_refuses_a_foreign_tool_name(engine):
    out = engine.execute({"tool": "helper"}, only="crisis")
    assert out["results"]["crisis"]["refused"] is True
    assert out["results"]["crisis"]["check"] == "naming"


# ---------------------------------------------------------------------------
# Prohibited uses: mem20liez.gates.check_prohibited_uses
# ---------------------------------------------------------------------------


def test_permitted_use_passes():
    assert governance.check_intended_uses(["incident_triage"]) == ("incident_triage",)


def test_no_declared_uses_passes():
    assert governance.check_intended_uses(None) == ()


def test_prohibited_use_is_refused_by_gate():
    with pytest.raises(governance.MeshRefused) as exc:
        governance.check_intended_uses(["automated_detention"])
    assert exc.value.check == "prohibited_use"


def test_prohibited_use_normalises_spacing_and_case():
    with pytest.raises(governance.MeshRefused):
        governance.check_intended_uses(["  Automated Detention  "])


def test_execute_refuses_a_prohibited_use(engine):
    out = engine.execute({"intended_uses": ["clinical_diagnosis"]}, only="crisis")
    assert out["results"]["crisis"]["refused"] is True
    assert out["results"]["crisis"]["check"] == "prohibited_use"


# ---------------------------------------------------------------------------
# Stub bodies: mem20verify.linters.noop_bodies
# ---------------------------------------------------------------------------


def test_real_mesh_source_has_no_stub_bodies(engine):
    from mem20meshz.runtime import MESHES, _mesh_dir

    for name, mod in MESHES.items():
        assert governance.audit_mesh_source(_mesh_dir(mod)) == []


def test_stub_body_is_refused_by_linter(tmp_path):
    (tmp_path / "stub.py").write_text("def operate(payload):\n    pass\n")
    with pytest.raises(governance.MeshRefused) as exc:
        governance.check_no_stubs(tmp_path)
    assert exc.value.check == "stub_body"


# ---------------------------------------------------------------------------
# Operating window: mem20temporaldatabasefabricz.temporal.interval.contains
# ---------------------------------------------------------------------------


def test_instant_inside_window_passes():
    cfg = {"valid_from": "2026-01-01T00:00:00Z", "valid_to": "2027-01-01T00:00:00Z"}
    assert governance.check_operating_window(cfg, "2026-06-01T00:00:00Z") is True


def test_instant_after_window_is_refused():
    cfg = {"valid_from": "2026-01-01T00:00:00Z", "valid_to": "2027-01-01T00:00:00Z"}
    with pytest.raises(governance.MeshRefused) as exc:
        governance.check_operating_window(cfg, "2027-06-01T00:00:00Z")
    assert exc.value.check == "outside_window"


def test_open_ended_window_passes():
    assert governance.check_operating_window({}, "2030-01-01T00:00:00Z") is True


def test_execute_refuses_an_instant_outside_the_window(engine):
    """A mesh with a declared window must refuse an instant outside it.

    The shipped CAPABILITY.json files declare no window (an open interval), so
    the window is set here rather than assumed -- otherwise this test would pass
    for the wrong reason.
    """
    original = engine.configs["crisis"]
    engine.configs["crisis"] = {
        **original,
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2027-01-01T00:00:00Z",
    }
    try:
        out = engine.execute({"at": "2099-01-01T00:00:00Z"}, only="crisis")
    finally:
        engine.configs["crisis"] = original
    assert out["results"]["crisis"]["refused"] is True
    assert out["results"]["crisis"]["check"] == "outside_window"


# ---------------------------------------------------------------------------
# Wire filter: mem20ircz.filter.classify + NoiseMeter
# ---------------------------------------------------------------------------


def test_human_channel_message_carries_signal():
    kept, meter = governance.filter_wire(
        [{"command": "PRIVMSG", "text": "the east wing is flooding",
          "prefix": "ana!u@h", "params": ("#ops",)}]
    )
    assert len(kept) == 1
    assert meter.kept == 1


def test_motd_numeric_is_noise():
    kept, meter = governance.filter_wire([{"command": "372", "text": "- motd"}])
    assert kept == []
    assert meter.by_reason["numeric.motd"] == 1


def test_notice_is_noise():
    kept, meter = governance.filter_wire(
        [{"command": "NOTICE", "text": "identify", "params": ("me",)}]
    )
    assert kept == []
    assert meter.by_reason["notice"] == 1


def test_mixed_lines_keep_only_the_signal():
    kept, meter = governance.filter_wire([
        {"command": "001", "text": "welcome"},
        {"command": "PRIVMSG", "text": "pump 3 is down", "prefix": "ana!u@h",
         "params": ("#ops",)},
        {"command": "JOIN", "params": ("#ops",)},
    ])
    assert [line.text for line in kept] == ["pump 3 is down"]
    assert meter.seen == 3 and meter.swallowed == 2
    assert 0.0 < meter.waste_ratio < 1.0


def test_execute_reports_wire_savings(engine):
    engine.execute({
        "wire": [
            {"command": "372", "text": "- motd"},
            {"command": "PRIVMSG", "text": "pump 3 is down", "prefix": "ana!u@h",
             "params": ("#ops",)},
        ]
    }, only="crisis")
    adm = engine.admission_report()["crisis"]
    assert adm["wire_kept"] == 1
    assert adm["wire_swallowed"] == 1
    assert adm["wire_reasons"] == {"numeric.motd": 1}


# ---------------------------------------------------------------------------
# Provenance: mem20dreamz.ledger.commit_raw
# ---------------------------------------------------------------------------


def test_provenance_reports_durability_honestly():
    record = governance.record_provenance("crisis", {"text": "x"}, {"ok": True})
    assert "committed" in record
    if record["committed"]:
        assert record["cid"]
    else:
        assert record["reason"]


# ---------------------------------------------------------------------------
# Governance keys must not leak into a mesh's domain input.
# ---------------------------------------------------------------------------


def test_governance_keys_are_stripped_before_dispatch(engine):
    from mem20meshz.runtime import GOVERNANCE_KEYS

    assert "intended_uses" in GOVERNANCE_KEYS
    assert "wire" in GOVERNANCE_KEYS
    out = engine.execute({"text": "demo", "intended_uses": ["incident_triage"]},
                         only="crisis")
    assert "refused" not in out["results"]["crisis"]
