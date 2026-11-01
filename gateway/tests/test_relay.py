"""Relay admission control must actually run before a message is written.

The gateway is the estate's deception surface: ``send_human_message`` posts as a
human, and a relay that will carry anything will carry an impersonation. These
tests drive the real entry points -- ``broadcast``, ``read_messages`` and the
tool catalog -- against a temporary gateway directory, and assert on what the
estate modules decided, not on a mock of them.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import pytest

import relay


@pytest.fixture()
def gw(tmp_path, monkeypatch):
    """Point the gateway at a temp dir and reload the modules against it."""
    monkeypatch.setenv("MEM20_GATEWAY_DIR", str(tmp_path))
    for mod in ("hermes_gateway", "gateway_tools", "mem20_gateway"):
        sys.modules.pop(mod, None)
    import hermes_gateway

    hermes_gateway.GATEWAY_DIR = tmp_path
    hermes_gateway.NAMES_FILE = tmp_path / "agent_names.json"
    hermes_gateway.MESSAGES_FILE = tmp_path / "messages.jsonl"
    return hermes_gateway


# ---------------------------------------------------------------------------
# The wiring itself: six estate modules, imported and called.
# ---------------------------------------------------------------------------


def test_relay_imports_six_estate_modules():
    from mem20liez.gates import check_prohibited_uses
    from mem20ops.clicheck import classify_naming
    from mem20verify.linters import noop_bodies
    from mem20ircz.filter import NoiseMeter, classify
    from mem20temporaldatabasefabricz.temporal.interval import contains
    from mem20dreamz import ledger

    assert relay.check_prohibited_uses is check_prohibited_uses
    assert relay.classify_naming is classify_naming
    assert relay.noop_bodies is noop_bodies
    assert relay.classify_wire_line is classify
    assert relay.NoiseMeter is NoiseMeter
    assert relay.interval_contains is contains
    assert relay.dreamz_ledger is ledger


# ---------------------------------------------------------------------------
# Naming: mem20ops.clicheck.classify_naming
# ---------------------------------------------------------------------------


def test_generated_name_is_an_estate_address():
    name = relay.generate_agent_name("sidney", "abc12345")
    assert name == "mem20-sidney-abc12345"
    assert relay.check_agent_name(name) == "mem20-native"


def test_hermes_prefixed_name_is_refused():
    """The old generator produced this, and it is not an address."""
    with pytest.raises(relay.RelayRefused) as exc:
        relay.check_agent_name("hermes-sidney-abc12345")
    assert exc.value.check == "naming"


def test_register_agent_generates_a_conforming_name(gw):
    record = gw.register_agent(location="sidney")
    assert record["naming"] == "mem20-native"
    assert record["name"].startswith("mem20-sidney-")


def test_register_agent_refuses_an_explicit_foreign_name(gw):
    with pytest.raises(relay.RelayRefused) as exc:
        gw.register_agent(name="helper")
    assert exc.value.check == "naming"


# ---------------------------------------------------------------------------
# Prohibited uses: mem20liez.gates.check_prohibited_uses
# ---------------------------------------------------------------------------


def test_permitted_use_passes():
    assert relay.check_intended_uses(["fleet_status"]) == ("fleet_status",)


def test_prohibited_use_is_refused():
    with pytest.raises(relay.RelayRefused) as exc:
        relay.check_intended_uses(["automated_detention"])
    assert exc.value.check == "prohibited_use"


def test_broadcast_refuses_a_prohibited_use_and_writes_nothing(gw):
    gw.register_agent(name="mem20-a-1", location="a")
    with pytest.raises(relay.RelayRefused):
        gw.broadcast("hello", agent_name="mem20-a-1",
                     intended_uses=["automated_detention"])
    assert not gw.MESSAGES_FILE.exists()


def test_broadcast_writes_an_admitted_message(gw):
    gw.register_agent(name="mem20-a-1", location="a")
    entry = gw.broadcast("pump 3 is down", agent_name="mem20-a-1",
                         intended_uses=["fleet_status"])
    assert entry["admission"]["naming"] == "mem20-native"
    assert entry["admission"]["intended_uses"] == ["fleet_status"]
    assert gw.MESSAGES_FILE.exists()


# ---------------------------------------------------------------------------
# Stub bodies: mem20verify.linters.noop_bodies
# ---------------------------------------------------------------------------


def test_real_gateway_source_has_no_stub_bodies():
    from pathlib import Path

    assert relay.audit_gateway_source(Path(HERE)) == []


def test_stub_body_is_refused(tmp_path):
    (tmp_path / "stub.py").write_text("def relay_it(msg):\n    pass\n")
    with pytest.raises(relay.RelayRefused) as exc:
        relay.check_no_stubs(tmp_path)
    assert exc.value.check == "stub_body"


# ---------------------------------------------------------------------------
# Message window: mem20temporaldatabasefabricz.temporal.interval.contains
# ---------------------------------------------------------------------------


def test_instant_inside_window_passes():
    assert relay.check_message_window(
        "2026-01-01T00:00:00Z", "2027-01-01T00:00:00Z", "2026-06-01T00:00:00Z"
    ) is True


def test_replayed_old_message_is_refused():
    with pytest.raises(relay.RelayRefused) as exc:
        relay.check_message_window(
            "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", "2026-06-01T00:00:00Z"
        )
    assert exc.value.check == "outside_window"


def test_open_window_passes():
    assert relay.check_message_window(None, None, "2030-01-01T00:00:00Z") is True


# ---------------------------------------------------------------------------
# Wire filter: mem20ircz.filter.classify + NoiseMeter
# ---------------------------------------------------------------------------


def test_motd_is_noise():
    kept, meter = relay.filter_wire([{"command": "372", "text": "- motd"}])
    assert kept == []
    assert meter.by_reason["numeric.motd"] == 1


def test_human_line_is_signal():
    kept, meter = relay.filter_wire(
        [{"command": "PRIVMSG", "text": "pump 3 is down", "prefix": "ana!u@h",
          "params": ("#ops",)}]
    )
    assert len(kept) == 1
    assert meter.kept == 1


def test_broadcast_reports_wire_savings(gw):
    gw.register_agent(name="mem20-a-1", location="a")
    entry = gw.broadcast(
        "pump 3 is down",
        agent_name="mem20-a-1",
        wire=[
            {"command": "372", "text": "- motd"},
            {"command": "PRIVMSG", "text": "pump 3 is down", "prefix": "ana!u@h",
             "params": ("#ops",)},
        ],
    )
    assert entry["admission"]["wire_kept"] == 1
    assert entry["admission"]["wire_swallowed"] == 1
    assert entry["wire"] == ["pump 3 is down"]


# ---------------------------------------------------------------------------
# Provenance: mem20dreamz.ledger.commit_raw
# ---------------------------------------------------------------------------


def test_broadcast_records_provenance(gw):
    gw.register_agent(name="mem20-a-1", location="a")
    entry = gw.broadcast("hello", agent_name="mem20-a-1")
    assert "provenance" in entry
    assert "committed" in entry["provenance"]
    if not entry["provenance"]["committed"]:
        assert entry["provenance"]["reason"]


# ---------------------------------------------------------------------------
# The read_messages KeyError: entries carry agent_name, not agent.
# ---------------------------------------------------------------------------


def test_read_messages_does_not_raise_keyerror(gw, capsys):
    gw.register_agent(name="mem20-a-1", location="a")
    gw.broadcast("hello", agent_name="mem20-a-1")
    messages = gw.read_messages()
    assert len(messages) == 1
    assert "mem20-a-1" in capsys.readouterr().out


def test_read_messages_filters_by_agent_name(gw):
    gw.register_agent(name="mem20-a-1", location="a")
    gw.register_agent(name="mem20-b-1", location="b")
    gw.broadcast("from a", agent_name="mem20-a-1")
    gw.broadcast("from b", agent_name="mem20-b-1")
    assert [m["message"] for m in gw.read_messages(agent="mem20-a-1")] == ["from a"]


# ---------------------------------------------------------------------------
# send_human_message is the impersonation surface: it must require a use.
# ---------------------------------------------------------------------------


def test_human_message_without_declared_use_is_refused(gw):
    import gateway_tools

    result = gateway_tools.tool_send_human_message("the board approved it")
    assert result["refused"] is True
    assert result["check"] == "undeclared_use"
    assert not gw.MESSAGES_FILE.exists()


def test_human_message_with_prohibited_use_is_refused(gw):
    import gateway_tools

    result = gateway_tools.tool_send_human_message(
        "the board approved it", intended_uses=["automated_detention"]
    )
    assert result["refused"] is True
    assert result["check"] == "prohibited_use"
    assert not gw.MESSAGES_FILE.exists()


def test_human_message_with_declared_use_is_written(gw):
    import gateway_tools

    result = gateway_tools.tool_send_human_message(
        "the board approved it", intended_uses=["operator_announcement"]
    )
    assert result["type"] == "human_message"
    assert result["admission"]["intended_uses"] == ["operator_announcement"]
    assert gw.MESSAGES_FILE.exists()


def test_direct_message_goes_through_admission(gw):
    import gateway_tools

    gw.register_agent(name="mem20-a-1", location="a")
    gw.register_agent(name="mem20-b-1", location="b")
    result = gateway_tools.tool_send_to_agent(
        "hi", "mem20-b-1", agent_name="mem20-a-1",
        intended_uses=["automated_detention"],
    )
    assert result["refused"] is True
    assert not gw.MESSAGES_FILE.exists()


# ---------------------------------------------------------------------------
# The two gateway modules must not drift again.
# ---------------------------------------------------------------------------


def test_mem20_gateway_reexports_the_one_implementation(gw):
    import mem20_gateway

    assert mem20_gateway.broadcast is gw.broadcast
    assert mem20_gateway.register_agent is gw.register_agent
