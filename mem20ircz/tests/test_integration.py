"""End-to-end tests for the cross-module integration.

These are not import smoke tests. Each one calls a real function in another
subsystem and asserts on its real return value, so a decorative import would
fail here rather than pass silently.
"""
from __future__ import annotations

import pytest

from mem20ircz.hub import ChatMessage
from mem20ircz import integration

#: Assembled at runtime so this file does not trip the repo's own secret
#: scanner. It is a fixture, not a credential.
FAKE_TOKEN = "gh" + "p_" + "0123456789abcdef"


def _msg(text: str, seq: int = 1, nick: str = "alice") -> ChatMessage:
    return ChatMessage(seq=seq, ts=0.0, nick=nick, target="#test", text=text)


class TestScreenMessage:
    def test_clean_message_has_no_findings(self):
        assert integration.screen_message(_msg("hello there")) == []

    def test_credential_shaped_message_is_flagged(self):
        findings = integration.screen_message(
            _msg("my token is " + FAKE_TOKEN)
        )
        assert findings, "a message containing a token must be flagged"
        assert findings[0]["seq"] == 1
        assert findings[0]["nick"] == "alice"
        # severity/kind come from mem20secretz, not from this module
        assert isinstance(findings[0]["severity"], str)
        assert isinstance(findings[0]["kind"], str)

    def test_password_word_is_flagged(self):
        findings = integration.screen_message(_msg("password=hunter2"))
        assert findings


class TestMessageCost:
    def test_short_message_costs_at_least_one_token(self):
        result = integration.message_cost(_msg("hi"))
        assert result["tokens"] >= 1
        assert result["chars"] == 2

    def test_cost_scales_with_length(self):
        result = integration.message_cost(_msg("x" * 400))
        assert result["tokens"] == 100


class TestPersistMessage:
    def test_message_round_trips_through_the_ledger(self):
        result = integration.persist_message(
            _msg("durable line", seq=7), topic="ircz/test-roundtrip"
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


class TestIntegrity:
    def test_store_roundtrip_check_runs(self):
        result = integration._run_integrity_check()
        assert "ok" in result
        assert "roundtrip_ok" in result


class TestIdentity:
    def test_identity_state_is_readable(self):
        result = integration.identity_snapshot()
        assert isinstance(result["namespace_count"], int)
        assert isinstance(result["pinned_block_count"], int)


class TestAuditMessage:
    def test_audit_calls_every_module(self):
        result = integration.audit_message(_msg("audited line", seq=11))
        assert result["seq"] == 11
        assert result["clean"] is True
        assert result["cost"]["tokens"] >= 1
        assert result["persisted"]["written"] is not None
        assert result["registration"]["registered"] is True
        assert "agents" in result["fleet"]
        assert "roundtrip_ok" in result["integrity"]
        assert "namespace_count" in result["identity"]

    def test_audit_flags_a_leak_but_still_persists(self):
        result = integration.audit_message(
            _msg("token: " + FAKE_TOKEN, seq=12)
        )
        assert result["clean"] is False
        assert result["findings"]
        # the message is still delivered and persisted -- screening informs,
        # it does not censor
        assert result["persisted"]["written"] is not None
