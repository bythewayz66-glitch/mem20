"""Regression tests for gateway.hermes_gateway message reading.

The defect these lock down: `read_messages()` filtered on `m["agent"]`, but
`broadcast()` stores the sender under `agent_name`. Any real broadcast entry
therefore raised `KeyError: 'agent'` as soon as `--agent` was passed, so the
`agents read --agent` path never worked against an actual message store.

Each test points the module's store at a tmp directory, so nothing here reads
or writes the real `/opt/mem20/gateway` files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from gateway import hermes_gateway as hg  # noqa: E402


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Point the gateway store at an isolated tmp directory."""
    gateway_dir = tmp_path / "gateway"
    monkeypatch.setattr(hg, "GATEWAY_DIR", gateway_dir)
    monkeypatch.setattr(hg, "NAMES_FILE", gateway_dir / "agent_names.json")
    monkeypatch.setattr(hg, "MESSAGES_FILE", gateway_dir / "messages.jsonl")
    return gateway_dir


def _register(name: str) -> None:
    record = hg.register_agent(name=name, location="test-node")
    assert record["name"] == name


# ---------------------------------------------------------------------------
# the regression itself
# ---------------------------------------------------------------------------
def test_broadcast_then_read_filtered_by_agent(store, capsys):
    """Broadcast from two agents, then read back filtered by one of them.

    This is the exact path that used to raise KeyError: the filter compared
    `m["agent"]`, a key that broadcast entries do not have.
    """
    _register("hermes-alpha")
    _register("hermes-beta")

    hg.broadcast("alpha reporting in", agent_name="hermes-alpha")
    hg.broadcast("beta reporting in", agent_name="hermes-beta")
    capsys.readouterr()  # drop the broadcast chatter

    # Must not raise.
    only_alpha = hg.read_messages(agent="hermes-alpha")

    assert len(only_alpha) == 1, "filter must select exactly the alpha entry"
    assert only_alpha[0]["agent_name"] == "hermes-alpha"
    assert only_alpha[0]["message"] == "alpha reporting in"

    out = capsys.readouterr().out
    assert "hermes-alpha" in out
    assert "hermes-beta" not in out


def test_unfiltered_read_returns_every_broadcast(store, capsys):
    _register("hermes-alpha")
    _register("hermes-beta")
    hg.broadcast("one", agent_name="hermes-alpha")
    hg.broadcast("two", agent_name="hermes-beta")
    capsys.readouterr()

    everything = hg.read_messages()

    assert len(everything) == 2
    assert {m["agent_name"] for m in everything} == {"hermes-alpha", "hermes-beta"}


def test_filter_for_absent_agent_returns_empty(store, capsys):
    _register("hermes-alpha")
    hg.broadcast("hello", agent_name="hermes-alpha")
    capsys.readouterr()

    assert hg.read_messages(agent="hermes-nobody") == []


# ---------------------------------------------------------------------------
# both record shapes, plus a record carrying neither key
# ---------------------------------------------------------------------------
def test_legacy_agent_key_is_also_matched(store, capsys):
    """Older/foreign writers use `agent`; the filter must accept that too."""
    store.mkdir(parents=True, exist_ok=True)
    legacy = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "agent": "hermes-legacy",
        "message": "written by an older gateway",
    }
    hg.MESSAGES_FILE.write_text(json.dumps(legacy) + "\n")

    found = hg.read_messages(agent="hermes-legacy")

    assert len(found) == 1
    assert hg._agent_of(found[0]) == "hermes-legacy"


def test_agent_of_prefers_agent_name_then_agent_then_empty():
    assert hg._agent_of({"agent_name": "a", "agent": "b"}) == "a"
    assert hg._agent_of({"agent": "b"}) == "b"
    assert hg._agent_of({}) == ""


def test_record_with_neither_key_does_not_raise(store, capsys):
    """A malformed record must not take down the whole read."""
    store.mkdir(parents=True, exist_ok=True)
    hg.MESSAGES_FILE.write_text(
        json.dumps({"timestamp": "2026-01-01T00:00:00+00:00", "message": "no sender"}) + "\n"
    )

    # Filtering for anything must simply exclude it, not raise.
    assert hg.read_messages(agent="hermes-alpha") == []

    # And an unfiltered read must still render it.
    everything = hg.read_messages()
    assert len(everything) == 1
    assert "no sender" in capsys.readouterr().out


def test_mixed_shapes_are_read_together(store, capsys):
    """A store holding both shapes filters correctly on either name."""
    store.mkdir(parents=True, exist_ok=True)
    hg.MESSAGES_FILE.write_text(
        json.dumps({"timestamp": "2026-01-01T00:00:00+00:00",
                    "agent_name": "new-style", "message": "n"}) + "\n"
        + json.dumps({"timestamp": "2026-01-02T00:00:00+00:00",
                      "agent": "old-style", "message": "o"}) + "\n"
    )

    assert [m["message"] for m in hg.read_messages(agent="new-style")] == ["n"]
    assert [m["message"] for m in hg.read_messages(agent="old-style")] == ["o"]
    assert len(hg.read_messages()) == 2


# ---------------------------------------------------------------------------
# the CLI path that surfaced the bug
# ---------------------------------------------------------------------------
def test_cli_agents_read_filtered_by_agent(store, monkeypatch, capsys):
    """`agents read --agent X` must not raise against a real message store.

    Note: `read_messages()` prints a human-readable listing to stdout before
    the CLI emits its JSON, so with `--json` the JSON is not the whole of
    stdout. That pre-existing stdout/JSON interleaving is a separate defect
    (not part of the agent-name fix), so this test extracts the JSON object
    rather than requiring stdout to be pure JSON.
    """
    from gateway.cli import main as cli_main

    _register("hermes-alpha")
    _register("hermes-beta")
    hg.broadcast("from alpha", agent_name="hermes-alpha")
    hg.broadcast("from beta", agent_name="hermes-beta")
    capsys.readouterr()

    code = cli_main(["--json", "agents", "read", "--agent", "hermes-alpha"])

    assert code == 0
    out = capsys.readouterr().out
    payload = json.loads(out[out.index("{"):])
    assert payload["ok"] is True
    assert payload["count"] == 1
    assert payload["messages"][0]["message"] == "from alpha"
