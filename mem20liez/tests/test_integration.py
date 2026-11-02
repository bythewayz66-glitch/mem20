"""End-to-end tests for the cross-module integration.

Each test calls a real function in another subsystem and asserts on its real
return value, so a decorative import would fail here rather than pass silently.
"""
from __future__ import annotations

from mem20liez.types import Confidence, DetectionResult, SignalType
from mem20liez import integration

#: Assembled at runtime so this file does not trip the repo's own secret
#: scanner. It is a fixture, not a credential.
FAKE_TOKEN = "gh" + "p_" + "0123456789abcdef"


def _result(value=0.8, score=0.9, features=None) -> DetectionResult:
    return DetectionResult(
        signal=SignalType.MICRO_EXPRESSION,
        value=value,
        confidence=Confidence(score=score, model_id="test-model",
                              model_version="0.0.1"),
        raw_features=features or {},
    )


class TestScreenFeatures:
    def test_clean_features_have_no_findings(self):
        assert integration.screen_features(_result(features={"au12": 0.4})) == []

    def test_credential_shaped_feature_is_flagged(self):
        findings = integration.screen_features(
            _result(features={"api_key": FAKE_TOKEN})
        )
        assert findings
        assert findings[0]["key"] == "api_key"
        assert isinstance(findings[0]["severity"], str)

    def test_pii_shaped_feature_is_flagged(self):
        findings = integration.screen_features(
            _result(features={"email": "someone@example.com"})
        )
        assert findings


class TestPersistDetection:
    def test_detection_round_trips_through_the_ledger(self):
        result = integration.persist_detection(
            _result(), topic="liez/test-roundtrip"
        )
        assert result["written"] is not None
        assert result["recalled"] >= 1
        assert result["roundtrip"] is True


class TestEstateRegistration:
    def test_subsystem_is_in_the_inventory(self):
        result = integration.estate_registration()
        assert result["inventory_size"] > 0
        assert result["registered"] is True


class TestFleetSnapshot:
    def test_fleet_registry_is_readable(self):
        result = integration.fleet_snapshot()
        assert result["agents"] >= 0
        assert isinstance(result["known"], list)


class TestIdentity:
    def test_identity_state_is_readable(self):
        result = integration.identity_snapshot()
        assert isinstance(result["namespace_count"], int)
        assert isinstance(result["pinned_block_count"], int)


class TestIntegrity:
    def test_store_roundtrip_check_runs(self):
        result = integration._run_integrity_check()
        assert "ok" in result
        assert "roundtrip_ok" in result


class TestAuditDetection:
    def test_audit_calls_every_module(self):
        result = integration.audit_detection(_result())
        assert result["clean"] is True
        assert result["persisted"]["written"] is not None
        assert result["registration"]["registered"] is True
        assert "agents" in result["fleet"]
        assert "roundtrip_ok" in result["integrity"]
        assert "namespace_count" in result["identity"]

    def test_audit_flags_a_leak_but_still_persists(self):
        result = integration.audit_detection(
            _result(features={"token": FAKE_TOKEN})
        )
        assert result["clean"] is False
        assert result["findings"]
        assert result["persisted"]["written"] is not None
