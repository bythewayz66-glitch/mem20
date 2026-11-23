"""Criterion-6 tests: every estate dependency is *called*, on a tested path.

Each test drives a real path in this package that cannot complete without
calling a sibling mem20 project, then asserts on that project's real result. If
any of the six calls is removed, stubbed or made a no-op, a test here fails -
which is the only version of criterion 6 that means anything.

The static checks at the bottom close the loophole directly: an estate import
must flow into a call, and no estate import may be annotated ``# noqa: F401``.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from mem20webhooksupernetworkz import domain, estate
from mem20webhooksupernetworkz.domain import (
    DeliveryLedger, PayloadRefusedError, WebhookSuperNetwork,
    WebhookVerificationError,
)

TS = 1_772_323_200.0     # 2026-03-01T00:00:00Z
BODY = '{"deploy":"staging","sha":"abc123"}'
SECRET = "s3cret"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Keep the suite from touching a developer's real store."""
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "mem20_store"))
    yield


@pytest.fixture()
def receiver(tmp_path):
    return WebhookSuperNetwork(SECRET, tolerance_seconds=300,
                               ledger_path=str(tmp_path / "delivered.txt"))


# -- the seam is reachable at all ------------------------------------------

class TestEstateReachability:
    def test_every_estate_project_imports(self):
        status = estate.estate_status()
        assert status["unavailable"] == {}, status["unavailable"]
        assert len(status["wired"]) >= 5, status

    def test_the_six_wired_projects_are_named(self):
        assert set(estate.estate_status()["wired"]) == {
            "mem20secretz", "mem20liez", "mem20verify", "mem20ops",
            "memory_engine", "toolchest"}

    def test_estate_path_is_idempotent(self):
        assert estate.estate_path() == []
        assert estate.estate_path() == []


class TestSingleEngineInstance:
    """The estate loads one file under two names; they must be one module.

    ``memory_engine/memory.py`` is imported as ``memory_engine.memory`` (as a
    package submodule) and as ``memory`` (from the directory on ``sys.path``).
    Python caches those as two independent modules, so ``STORE_DIR``/``LEDGER``
    and the vector/BM25 indexes exist twice for one store.

    The damage is a false negative that looks like data corruption: after a test
    or a supervisor changes ``MEM20_STORE_PATH``, one copy keeps the old path,
    ``mem20verify.dataintegrity`` writes through the stale copy and then reports
    "no ledger row written" - an integrity failure on a healthy store. That
    blocked every replay until the loader was fixed, so it is pinned here.
    """

    def test_the_two_names_are_the_same_module(self):
        import memory as by_plain_name
        import memory_engine.memory as by_package_name

        assert by_plain_name is by_package_name, (
            "memory and memory_engine.memory are two copies of one file; their "
            "STORE_DIR/LEDGER constants can disagree")

    def test_a_moved_store_is_seen_by_both_names(self, tmp_path, monkeypatch):
        """Point the store somewhere new; both names must agree on it."""
        moved = str(tmp_path / "moved_store")
        monkeypatch.setenv("MEM20_STORE_PATH", moved)
        # A fresh interpreter per test would not exercise this; the alias plus
        # an explicit resync is what a long-lived process does.
        assert estate.resync_engine_store() is True

        import memory as by_plain_name
        import memory_engine.memory as by_package_name

        assert by_plain_name.LEDGER == by_package_name.LEDGER
        assert by_package_name.LEDGER.startswith(moved)

    def test_verify_succeeds_after_the_store_moved(self, tmp_path, monkeypatch):
        """The end-to-end consequence: a healthy store is not called damaged."""
        monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "another_store"))
        assert estate.resync_engine_store() is True
        report = estate.verify_store()
        assert report["ok"] is True, report["failures"][:3]
        assert report["roundtrip_ok"] == report["checked"]


# -- 1. memory_engine: is the sender's event time legal? ------------------

class TestEventTime:
    def test_an_epoch_timestamp_is_normalised_by_the_ledger(self):
        assert estate.validate_event_time(TS) == "2026-03-01T00:00:00+00:00"

    def test_a_typo_event_time_is_refused_by_the_engine(self):
        with pytest.raises(ValueError, match="ISO-8601"):
            estate.validate_event_time("2026")

    def test_a_wildly_future_event_time_is_refused(self):
        with pytest.raises(ValueError):
            estate.validate_event_time("2099-01-01T00:00:00+00:00")

    def test_deliver_returns_the_normalised_event_time(self, receiver):
        """The delivery path really calls the validator: its verdict is returned."""
        sig = receiver.sign(BODY, TS)
        outcome = receiver.deliver(BODY, TS, sig, now=TS, idempotency_key="k1")
        assert outcome["delivered"] is True
        assert outcome["event_time"] == "2026-03-01T00:00:00+00:00"


# -- 2. mem20secretz: may this payload be persisted? ----------------------

class TestPayloadAdmission:
    def test_a_credential_key_is_unsafe(self):
        verdict = estate.classify_payload({"api_token": "x"})
        assert verdict["safe"] is False
        assert verdict["severity"] == "critical"
        assert verdict["field"] == "api_token"

    def test_an_ordinary_payload_is_safe(self):
        verdict = estate.classify_payload({"deploy": "staging", "sha": "abc123"})
        assert verdict["safe"] is True
        assert verdict["kind"] == "none"

    def test_a_nested_credential_is_found(self):
        verdict = estate.classify_payload({"meta": {"auth": {"api_key": "x"}}})
        assert verdict["safe"] is False
        assert "api_key" in verdict["field"]

    def test_deliver_refuses_a_credential_payload(self, receiver):
        """The refusal is the point: the event log is durable and replayed."""
        sig = receiver.sign(BODY, TS)
        with pytest.raises(PayloadRefusedError, match="refusing to persist"):
            receiver.deliver(
                BODY, TS, sig, now=TS, idempotency_key="k1",
                payload={"api_token": "ghp_abc123def456ghi789jkl012mno345"})
        assert receiver.refused_payloads == 1
        assert len(receiver.delivered) == 0

    def test_deliver_admits_an_ordinary_payload(self, receiver):
        sig = receiver.sign(BODY, TS)
        outcome = receiver.deliver(BODY, TS, sig, now=TS, idempotency_key="k1",
                                   payload=json.loads(BODY))
        assert outcome["delivered"] is True
        assert outcome["admission"]["safe"] is True


# -- 3. mem20liez: may this route exist at all? ---------------------------

class TestRouteLegality:
    def test_ordinary_use_is_permitted(self):
        assert estate.check_route_legality(["webhook_routing"])["permitted"] is True

    def test_a_prohibited_use_raises_the_estate_gate_error(self):
        from mem20liez.gates import GateError
        with pytest.raises(GateError):
            estate.check_route_legality(["automated_detention"])

    def test_a_receiver_declared_for_a_prohibited_use_cannot_be_built(self):
        """Admissibility is decided at construction, not per request."""
        from mem20liez.gates import GateError
        with pytest.raises(GateError):
            WebhookSuperNetwork(SECRET, intended_uses=["clinical_diagnosis"])


# -- 4. mem20verify: can the store be replayed from? ----------------------

class TestReplayVerification:
    def test_a_replay_verifies_the_store_first(self, receiver):
        report = receiver.replay([
            {"body": BODY, "timestamp": TS, "signature": receiver.sign(BODY, TS),
             "now": TS, "idempotency_key": "r1"},
        ])
        assert report["store"]["ok"] is True
        assert report["replayed"] == 1

    def test_a_damaged_store_refuses_the_replay(self, receiver, monkeypatch):
        """A partial replay that looks complete is worse than a failed one."""
        from mem20webhooksupernetworkz import estate as seam

        def broken(_engine_dir=None):
            return {"ok": False, "error": "round-trip failed", "checked": 0,
                    "roundtrip_ok": 0, "failures": [{"x": 1}]}

        monkeypatch.setattr(seam, "verify_store", broken)
        monkeypatch.setattr(domain.estate, "verify_store", broken)
        with pytest.raises(ValueError, match="refusing to replay"):
            receiver.replay([{"body": BODY, "timestamp": TS,
                              "signature": receiver.sign(BODY, TS), "now": TS}])


# -- 5. mem20ops: which store is this? ------------------------------------

class TestStoreIdentity:
    def test_identity_comes_from_the_ops_checks(self):
        report = estate.identity()
        assert "store_path" in report
        assert "pinned_block_count" in report

    def test_the_receiver_reports_the_ops_identity(self, receiver):
        identity = receiver.store_identity()
        assert identity["store_path"] == os.environ["MEM20_STORE_PATH"]


# -- 6. toolchest: what may a route target? -------------------------------

class TestRouteCapabilities:
    def test_inventory_is_read_from_the_catalog(self):
        inventory = estate.tool_inventory()
        assert inventory["source"] == "toolchest.catalog.load_inventory"
        assert inventory["total"] > 100

    def test_the_receiver_exposes_the_measured_inventory(self, receiver):
        assert receiver.route_capabilities()["total"] > 100


# -- the signature/ledger defects this branch fixed -----------------------

class TestDeliveryLedger:
    def test_the_ledger_is_bounded(self):
        ledger = DeliveryLedger(max_entries=2)
        for key in ("a", "b", "c"):
            ledger.add(key)
        assert len(ledger) == 2
        assert "a" not in ledger

    def test_the_ledger_survives_a_restart(self, tmp_path):
        path = str(tmp_path / "ledger.txt")
        first = DeliveryLedger(path=path)
        first.add("k1")
        assert "k1" in DeliveryLedger(path=path)

    def test_a_restart_does_not_re_deliver(self, tmp_path):
        """The bug: an in-memory list forgot everything on restart."""
        path = str(tmp_path / "ledger.txt")
        sig = WebhookSuperNetwork(SECRET).sign(BODY, TS)
        one = WebhookSuperNetwork(SECRET, ledger_path=path)
        assert one.deliver(BODY, TS, sig, now=TS,
                           idempotency_key="k1")["delivered"] is True
        two = WebhookSuperNetwork(SECRET, ledger_path=path)
        second = two.deliver(BODY, TS, sig, now=TS, idempotency_key="k1")
        assert second["delivered"] is False
        assert second["reason"] == "duplicate"

    def test_the_timestamp_is_inside_the_signature(self):
        """Signing the body alone would let the window be escaped."""
        receiver = WebhookSuperNetwork(SECRET)
        assert receiver.sign(BODY, TS) != receiver.sign(BODY, TS + 10)


# -- the MCP surface is reached through the real server -------------------

class TestMcpRegistration:
    """The subsystem must be reachable through the estate's MCP server.

    A tools file imported by nobody, or listed in a registry whose value is
    never dispatched, is the same decorative failure as an unused import - one
    level up. These tests import the real server module, build its real server
    object, and assert the tools are both listed and bound for dispatch.
    """

    @pytest.fixture()
    def server_module(self, monkeypatch):
        """Import ``mcp/server.py`` from the repo root."""
        import importlib
        import sys as _sys

        mcp_dir = estate.REPO_ROOT / "mcp"
        if not (mcp_dir / "server.py").is_file():
            pytest.skip("mcp/server.py not present")
        monkeypatch.setenv("MEM20_WEBHOOK_SECRET", SECRET)
        if str(mcp_dir) not in _sys.path:
            _sys.path.insert(0, str(mcp_dir))
        return importlib.import_module("server")

    def test_the_server_lists_the_webhook_tools(self, server_module):
        instance = server_module.Mem20MCPServer()
        names = {n for n in instance.tools if n.startswith("webhook_")}
        assert names == {"webhook_verify", "webhook_deliver", "webhook_replay",
                         "webhook_route_capabilities", "webhook_doctor"}

    def test_every_listed_tool_is_bound_for_dispatch(self, server_module):
        """The dispatcher's ``_<tool_name>`` convention must resolve."""
        instance = server_module.Mem20MCPServer()
        for name in ("webhook_verify", "webhook_deliver", "webhook_doctor"):
            assert hasattr(instance, f"_{name}"), (
                f"{name} is listed but has no _dispatch binding")

    @pytest.fixture()
    def tools_module(self):
        import importlib
        import sys as _sys

        mcp_tools = estate.REPO_ROOT / "mcp" / "tools"
        if not (mcp_tools / "webhook_tools.py").is_file():
            pytest.skip("mcp/tools/webhook_tools.py not present")
        if str(mcp_tools) not in _sys.path:
            _sys.path.insert(0, str(mcp_tools))
        return importlib.import_module("webhook_tools")

    def test_every_declared_tool_has_a_handler_and_schema(self, tools_module):
        for tool in tools_module.TOOLS:
            assert callable(tool["handler"]), tool["name"]
            assert tool["inputSchema"]["type"] == "object", tool["name"]
            assert tool["description"], tool["name"]

    def test_install_registers_on_a_server_object(self, tools_module):
        class FakeServer:
            def __init__(self):
                self.tools = {}

        server = FakeServer()
        registered = tools_module.install(server)
        assert registered == [t["name"] for t in tools_module.TOOLS]
        assert set(server.tools) == set(registered)

    def test_a_tool_round_trips_and_refuses_a_credential(self, tools_module,
                                                         monkeypatch):
        monkeypatch.setenv("MEM20_WEBHOOK_SECRET", SECRET)
        # ``webhook_deliver`` has no ``now`` override on purpose - a delivery tool
        # that accepts a caller-supplied clock is a replay hole - so this uses a
        # timestamp that is genuinely current, which is what a provider sends.
        live = round(time.time(), 3)
        sig = tools_module._receiver(secret=SECRET).sign(BODY, live)
        out = tools_module.handle("webhook_verify", {
            "body": BODY, "timestamp": live, "signature": sig,
            "secret": SECRET})
        assert out["signature_ok"] is True
        assert out["event_time"].startswith("20")

        refused = tools_module.handle("webhook_deliver", {
            "body": BODY, "timestamp": live, "signature": sig,
            "idempotency_key": "mcp-cred-1",
            "payload": json.dumps({"api_token": "ghp_abc123def456ghi789jkl012mno"}),
            "secret": SECRET})
        assert refused["delivered"] is False
        assert refused["refused"] == "PayloadRefusedError"

    def test_a_receiver_without_a_secret_refuses_to_start(self, tools_module,
                                                          monkeypatch):
        """An empty HMAC key accepts anything; refusing is the safe default."""
        monkeypatch.delenv("MEM20_WEBHOOK_SECRET", raising=False)
        with pytest.raises(ValueError, match="MEM20_WEBHOOK_SECRET"):
            tools_module._receiver()


# -- static proof the wiring is not decorative -----------------------------

class TestWiringIsNotDecorative:
    PKG = Path(estate.__file__).resolve().parent

    @pytest.mark.parametrize("symbol", [
        "_classify_secret", "_check_prohibited_uses", "_integrity_check",
        "_identity_check", "_validate_event_time", "_load_inventory",
    ])
    def test_each_estate_symbol_is_resolved_through_need(self, symbol):
        seam = (self.PKG / "estate.py").read_text(encoding="utf-8")
        assert f"need({symbol}," in seam, (
            f"{symbol} is imported but flows into no call - decorative import")

    @pytest.mark.parametrize("seam_call", [
        "estate.check_route_legality(", "estate.validate_event_time(",
        "estate.classify_payload(", "estate.verify_store(",
        "estate.identity(", "estate.tool_inventory(",
    ])
    def test_the_domain_calls_the_seam(self, seam_call):
        text = (self.PKG / "domain.py").read_text(encoding="utf-8")
        assert seam_call in text, f"domain.py does not call {seam_call}"

    def test_no_estate_import_is_annotated_as_unused(self):
        for name in ("estate.py", "domain.py", "cli.py"):
            text = (self.PKG / name).read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped.startswith(("from . import", "from mem20",
                                            "from memory_engine", "from toolchest")):
                    continue
                assert "F401" not in line and "noqa" not in line, (
                    f"decorative import in {name}: {stripped}")
