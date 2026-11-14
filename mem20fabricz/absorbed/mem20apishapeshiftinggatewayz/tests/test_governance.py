"""Admission control must actually run before a payload is transformed.

This gateway rewrites payloads, which is exactly where a field silently
disappears. These tests drive ``Engine.execute`` -- the same entry point the CLI
and the HTTP handler use -- and assert on what the estate modules decided, not
on a mock of them.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from mem20apishapeshiftinggatewayz import governance
from mem20apishapeshiftinggatewayz.runtime import Engine, load_config

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def config():
    return load_config(os.path.join(HERE, "CAPABILITY.json"))


@pytest.fixture()
def engine(config, tmp_path):
    return Engine(config, db_path=tmp_path / "state.sqlite3")


# ---------------------------------------------------------------------------
# The wiring itself: six estate modules, imported and called.
# ---------------------------------------------------------------------------


def test_governance_imports_six_estate_modules():
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


def test_execute_records_an_admission(engine):
    engine.execute({"goal": "route this", "candidates": [{"id": "a"}]})
    report = engine.admission_report()
    assert report
    for adm in report.values():
        assert adm["naming"] == "mem20-native"
        assert adm["stub_issues"] == 0
        assert adm["window_ok"] is True


def test_execute_records_provenance(engine):
    engine.execute({"goal": "route this", "candidates": [{"id": "a"}]})
    prov = engine.provenance_report()
    assert prov
    for record in prov.values():
        assert "committed" in record
        if not record["committed"]:
            assert record["reason"]


# ---------------------------------------------------------------------------
# Route naming: mem20ops.clicheck.classify_naming
# ---------------------------------------------------------------------------


def test_estate_route_is_admitted():
    assert governance.check_route("mem20_route") == "mem20-native"


def test_fs_route_is_admitted():
    assert governance.check_route("fs-route") == "fs-standard"


def test_foreign_route_is_refused():
    with pytest.raises(governance.GatewayRefused) as exc:
        governance.check_route("/api/v1/things")
    assert exc.value.check == "naming"


def test_execute_refuses_a_foreign_route(engine):
    with pytest.raises(governance.GatewayRefused) as exc:
        engine.execute({"route": "/api/v1/things", "goal": "x"})
    assert exc.value.check == "naming"


# ---------------------------------------------------------------------------
# Round trip: the shape-shifting bug is a field that disappears.
# ---------------------------------------------------------------------------


def test_identity_mapping_keeps_every_field():
    report = governance.check_round_trip({"goal": "x", "candidates": []}, {})
    assert report["fields_in"] == report["fields_out"] == 2


def test_renaming_mapping_keeps_every_field():
    report = governance.check_round_trip({"a": 1, "b": 2}, {"a": "mem20_a"})
    assert report["fields_out"] == 2
    assert report["mapping"] == {"a": "mem20_a"}


def test_collapsing_mapping_is_refused():
    """Two fields onto one key: one value silently disappears."""
    with pytest.raises(governance.GatewayRefused) as exc:
        governance.check_round_trip({"a": 1, "b": 2}, {"a": "same", "b": "same"})
    assert exc.value.check == "lossy_transform"


def test_execute_refuses_a_lossy_mapping(engine):
    with pytest.raises(governance.GatewayRefused) as exc:
        engine.execute({"goal": "x", "a": 1, "b": 2,
                        "mapping": {"a": "same", "b": "same"}})
    assert exc.value.check == "lossy_transform"


def test_payload_keys_are_domain_data_not_addresses(engine):
    """goal/candidates are ordinary words; only the route is an address."""
    out = engine.execute({"goal": "route this", "candidates": [{"id": "a"}]})
    assert "refused" not in out


# ---------------------------------------------------------------------------
# Prohibited uses: mem20liez.gates.check_prohibited_uses
# ---------------------------------------------------------------------------


def test_permitted_use_passes():
    assert governance.check_intended_uses(["schema_translation"]) == ("schema_translation",)


def test_prohibited_use_is_refused():
    with pytest.raises(governance.GatewayRefused) as exc:
        governance.check_intended_uses(["automated_detention"])
    assert exc.value.check == "prohibited_use"


def test_execute_refuses_a_prohibited_use(engine):
    with pytest.raises(governance.GatewayRefused) as exc:
        engine.execute({"goal": "x", "intended_uses": ["automated_detention"]})
    assert exc.value.check == "prohibited_use"


# ---------------------------------------------------------------------------
# Stub bodies: mem20verify.linters.noop_bodies
# ---------------------------------------------------------------------------


def test_real_gateway_source_has_no_stub_bodies():
    from pathlib import Path

    assert governance.audit_gateway_source(Path(HERE)) == []


def test_stub_body_is_refused(tmp_path):
    (tmp_path / "stub.py").write_text("def transform(payload):\n    pass\n")
    with pytest.raises(governance.GatewayRefused) as exc:
        governance.check_no_stubs(tmp_path)
    assert exc.value.check == "stub_body"


# ---------------------------------------------------------------------------
# Version window: mem20temporaldatabasefabricz.temporal.interval.contains
# ---------------------------------------------------------------------------


def test_version_inside_window_passes():
    assert governance.check_version_window(
        "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2026-06-01T00:00:00Z"
    ) is True


def test_retired_version_is_refused():
    with pytest.raises(governance.GatewayRefused) as exc:
        governance.check_version_window(
            "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", "2026-06-01T00:00:00Z"
        )
    assert exc.value.check == "outside_window"


def test_open_window_passes():
    assert governance.check_version_window(None, None, "2030-01-01T00:00:00Z") is True


def test_execute_refuses_a_retired_version(engine):
    with pytest.raises(governance.GatewayRefused) as exc:
        engine.execute({
            "goal": "x",
            "at": "2026-06-01T00:00:00Z",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_to": "2026-02-01T00:00:00Z",
        })
    assert exc.value.check == "outside_window"


# ---------------------------------------------------------------------------
# Upstream filter: mem20ircz.filter.classify + NoiseMeter
# ---------------------------------------------------------------------------


def test_health_probe_noise_is_dropped():
    kept, meter = governance.filter_wire([{"command": "372", "text": "- banner"}])
    assert kept == []
    assert meter.by_reason["numeric.motd"] == 1


def test_real_request_line_is_kept():
    kept, meter = governance.filter_wire(
        [{"command": "PRIVMSG", "text": "translate this", "prefix": "a!u@h",
          "params": ("#ops",)}]
    )
    assert len(kept) == 1
    assert meter.kept == 1


def test_execute_reports_wire_savings(engine):
    engine.execute({
        "goal": "x",
        "wire": [
            {"command": "372", "text": "- banner"},
            {"command": "PRIVMSG", "text": "translate this", "prefix": "a!u@h",
             "params": ("#ops",)},
        ],
    })
    adm = list(engine.admission_report().values())[-1]
    assert adm["wire_kept"] == 1
    assert adm["wire_swallowed"] == 1
    assert adm["wire_reasons"] == {"numeric.motd": 1}


# ---------------------------------------------------------------------------
# Provenance: mem20dreamz.ledger.commit_raw
# ---------------------------------------------------------------------------


def test_provenance_reports_durability_honestly():
    record = governance.record_provenance("mem20_route", {"goal": "x"}, {"ok": True})
    assert "committed" in record
    if record["committed"]:
        assert record["cid"]
    else:
        assert record["reason"]


# ---------------------------------------------------------------------------
# Governance keys must not leak into the operation's domain input.
# ---------------------------------------------------------------------------


def test_governance_keys_are_stripped_before_dispatch(engine):
    from mem20apishapeshiftinggatewayz.runtime import GOVERNANCE_KEYS

    assert "intended_uses" in GOVERNANCE_KEYS
    assert "route" in GOVERNANCE_KEYS
    out = engine.execute({"goal": "x", "intended_uses": ["schema_translation"]})
    assert "refused" not in out
