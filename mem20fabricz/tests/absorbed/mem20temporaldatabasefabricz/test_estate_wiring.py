"""Criterion-6 tests: every estate dependency is *called*, on a tested path.

These tests exist to make the wiring load-bearing rather than decorative. Each
one exercises a code path in this package that cannot complete without calling
into a sibling mem20 project, and then asserts on that project's real result.

The distinction that matters: ``import mem20secretz.sweep`` in a module nobody
calls proves nothing. Here, if any one of the seven estate calls is removed,
stubbed or made a no-op, a test below fails - which is the only version of
criterion 6 that means anything.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from mem20temporaldatabasefabricz.temporal import (
    engine as engine_module, estate, estate_calls, estate_surface,
    ledger_adapter,
)
from mem20temporaldatabasefabricz.temporal.engine import BiTemporalEngine
from mem20temporaldatabasefabricz.temporal.ledger_adapter import (
    ingest_ledger,
)
from mem20temporaldatabasefabricz.temporal.store import TemporalStore

T0 = "2026-03-01T00:00:00+00:00"
T1 = "2026-03-01T06:00:00+00:00"
T2 = "2026-03-01T12:00:00+00:00"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Point the memory engine at a throwaway store for every test here.

    ``mem20ops.memchecks`` reloads the engine when MEM20_STORE_PATH moves, so
    this also keeps the suite from touching a developer's real store.
    """
    monkeypatch.setenv("MEM20_STORE_PATH", str(tmp_path / "mem20_store"))
    yield


class Clock:
    def __init__(self, start: str = T0):
        self.at = start

    def __call__(self) -> str:
        return self.at


@pytest.fixture()
def engine(tmp_path):
    store = TemporalStore(tmp_path / "temporal.db")
    yield BiTemporalEngine(store, clock=Clock())
    store.close()


# -- the seam is reachable at all ------------------------------------------

class TestEstateReachability:
    def test_every_estate_project_imports(self):
        status = estate.estate_status()
        assert status["unavailable"] == {}, (
            f"estate projects unavailable: {status['unavailable']}")
        assert len(status["wired"]) >= 5, status

    def test_the_seven_wired_projects_are_named(self):
        wired = set(estate.estate_status()["wired"])
        assert wired == {"memory_engine", "mem20verify", "mem20ops",
                         "mem20secretz", "mem20liez", "mem20ircz", "toolchest"}

    def test_estate_path_is_idempotent(self):
        assert estate.estate_path() == []
        assert estate.estate_path() == []


# -- 1. memory_engine: event-time legality --------------------------------

class TestMemoryEngineEventTime:
    def test_legal_event_time_passes_through_normalised(self):
        assert estate_calls.validate_event_time("2026-10-01T00:00:00+00:00") == \
            "2026-10-01T00:00:00+00:00"

    def test_a_typo_event_time_is_refused(self):
        """The engine's own bounds, not a local parse check.

        ``"2026"`` parses as a year in some libraries; the ledger rejects it.
        This asserts we get *its* refusal, which is the whole reason to call it.
        """
        with pytest.raises(ValueError, match="ISO-8601"):
            estate_calls.validate_event_time("2026")

    def test_huge_future_skew_is_refused_by_the_engine(self):
        with pytest.raises(ValueError):
            estate_calls.validate_event_time("2099-01-01T00:00:00+00:00")

    def test_assert_belief_records_the_normalised_event_time(self, engine):
        """The write path really calls the validator: its stamp is in provenance."""
        interval = engine.assert_belief(
            "svc.port", "value", "8080", valid_from=T0, known_at=T1)
        stamp = interval.provenance["valid_from_normalised"]
        assert stamp == "2026-03-01T00:00:00+00:00"
        assert interval.provenance["event_time_validated_by"].endswith(
            "validate_event_time")

    def test_assert_belief_no_longer_accepts_a_bogus_event_time(self, engine):
        """Before the seam, an unparseable valid_from was stored as-is."""
        with pytest.raises(ValueError):
            engine.assert_belief("svc.port", "value", "8080", valid_from="2026")

    def test_ledger_rows_are_read_through_the_engine(self):
        assert isinstance(estate_calls.ledger_rows(), list)


# -- 2. mem20verify: is the ledger trustworthy? ---------------------------

class TestLedgerIntegrity:
    def test_integrity_check_runs_a_real_round_trip(self):
        result = estate_calls.verify_ledger_integrity()
        assert result["ok"] is True
        assert result["checked"] >= 1
        assert result["roundtrip_ok"] == result["checked"]

    def test_ingest_refuses_when_the_ledger_cannot_round_trip(
            self, tmp_path, monkeypatch):
        """A damaged authority must stop the ingest, not seed it."""
        def broken(_engine_dir=None):
            return {"ok": False, "error": "round-trip failed",
                    "checked": 3, "roundtrip_ok": 0, "failures": [{"x": 1}],
                    "false_positive_detections": []}

        monkeypatch.setattr(ledger_adapter, "verify_ledger_integrity", broken)
        store = TemporalStore(tmp_path / "t.db")
        try:
            with pytest.raises(ValueError, match="refusing to ingest"):
                ingest_ledger(store, verify=True)
        finally:
            store.close()

    def test_ingest_records_the_verification_it_performed(self, tmp_path):
        ledger = tmp_path / "ledger.jsonl"
        ledger.write_text(json.dumps({
            "action": "remember", "id": "r1", "topic": "deploy",
            "content": "target is staging", "ts": T1, "valid_from": T0,
            "event_time_basis": "declared", "actor": "test",
        }) + "\n", encoding="utf-8")
        store = TemporalStore(tmp_path / "t.db")
        try:
            report = ingest_ledger(store, str(ledger), verify=True)
        finally:
            store.close()
        assert report["verified"]["ok"] is True
        assert report["versions_in_store"] == 1


# -- 3. mem20ops: which store is this? -----------------------------------

class TestIdentity:
    def test_identity_comes_from_the_ops_checks(self):
        report = estate_calls.identity()
        assert "store_path" in report
        assert "pinned_block_count" in report
        assert "namespace_count" in report

    def test_engine_stamps_the_ops_identity_into_provenance(self, engine):
        interval = engine.assert_belief("svc.port", "value", "8080", known_at=T1)
        identity = interval.provenance["estate"]["identity"]
        assert identity["store_path"] == os.environ["MEM20_STORE_PATH"]

    def test_identity_is_computed_once_per_engine(self, engine, monkeypatch):
        """A per-write identity call would make every assertion a subprocess."""
        calls = []
        real = estate_calls.identity

        def counting(*a, **kw):
            calls.append(1)
            return real(*a, **kw)

        # Patch the consumer's binding, not the seam's: engine.py imports the
        # function by name, so the only way to intercept the call it makes is at
        # its own module attribute. That is also what makes the wiring real -
        # there is no indirection left for a caller to bypass.
        monkeypatch.setattr(engine_module, "identity", counting)
        engine.assert_belief("a", "v", "1", known_at=T1)
        engine.assert_belief("b", "v", "2", known_at=T1)
        assert len(calls) == 1


# -- 4. mem20secretz: never archive a credential -------------------------

class TestSecretRefusal:
    def test_a_credential_is_classified_unsafe(self):
        result = estate_calls.classify_secret("GITHUB_TOKEN",
                                        "ghp_abc123def456ghi789jkl012mno345")
        assert result["safe"] is False
        assert result["severity"] == "critical"
        assert result["kind"] == "credential"

    def test_an_endpoint_is_only_config(self):
        result = estate_calls.classify_secret("API_URL", "https://api.example.com")
        assert result["safe"] is True
        assert result["kind"] == "config"

    def test_asserting_a_credential_is_refused(self, engine):
        """The refusal is the feature: this store can never delete a row."""
        with pytest.raises(Exception, match="append-only|credential|refusing"):
            engine.assert_belief("creds", "token",
                                 "ghp_abc123def456ghi789jkl012mno345", known_at=T1)
        assert engine.store.count() == 0

    def test_correcting_into_a_credential_is_refused_too(self, engine):
        """The correction path re-admits: it writes a new version, so it is a write."""
        engine.assert_belief("svc.creds", "value", "configured-locally", known_at=T1)
        with pytest.raises(Exception, match="refusing|credential|append-only"):
            engine.correct("svc.creds", "value",
                           "ghp_abc123def456ghi789jkl012mno345", known_at=T2)

    def test_a_safe_value_records_its_class(self, engine):
        interval = engine.assert_belief("svc.port", "value", "8080", known_at=T1)
        assert interval.provenance["estate"]["value_class"]["safe"] is True


# -- 5. mem20liez: prohibited uses are refused at the seam ---------------

class TestLegalityGate:
    def test_ordinary_use_is_permitted(self):
        assert estate_calls.check_belief_legality(["memory_search"])["permitted"] is True

    def test_a_prohibited_use_raises_the_estate_gate_error(self):
        from mem20liez.gates import GateError
        with pytest.raises(GateError):
            estate_calls.check_belief_legality(["automated_detention"])

    def test_an_engine_declared_for_a_prohibited_use_cannot_write(self, tmp_path):
        store = TemporalStore(tmp_path / "t.db")
        try:
            engine = BiTemporalEngine(store, intended_uses=["clinical_diagnosis"])
            with pytest.raises(Exception, match="prohibited"):
                engine.assert_belief("patient", "risk", "low", known_at=T1)
            assert store.count() == 0
        finally:
            store.close()


# -- 6. mem20ircz: wire noise stays off the valid axis -------------------

class TestWireNoise:
    def test_the_classifier_separates_a_person_from_a_protocol_line(self):
        probe = estate_surface.wire_noise()
        assert probe["person_kept"] is True
        assert probe["protocol_kept"] is False
        assert probe["meter"] == "NoiseMeter"

    def test_a_message_is_not_noise(self):
        assert estate_surface.is_noise_line("deploy target is staging") is False

    def test_ingest_skips_noise_rows_and_counts_them(self, tmp_path):
        """A protocol line that reached the ledger must not become a belief.

        The row is written as a real wire line, because that is what the estate
        classifier classifies. A sentence that merely *describes* a join is
        content, and a test that treated it as noise would be asserting the
        wrong contract.
        """
        ledger = tmp_path / "ledger.jsonl"
        rows = [
            {"action": "remember", "id": "r1", "topic": "deploy",
             "content": "target is staging", "ts": T1},
            {"action": "remember", "id": "r2", "topic": "#ops",
             "content": ":alice!u@host JOIN #ops", "ts": T1},
        ]
        ledger.write_text("".join(json.dumps(r) + "\n" for r in rows),
                          encoding="utf-8")
        store = TemporalStore(tmp_path / "t.db")
        try:
            report = ingest_ledger(store, str(ledger), verify=False)
        finally:
            store.close()
        assert report["ledger_rows"] == 2
        assert report["skipped_noise"] == 1
        assert report["versions_in_store"] == 1


# -- 7. toolchest: what does the estate actually expose? ----------------

class TestToolInventory:
    def test_inventory_is_read_from_the_catalog(self):
        inventory = estate_surface.tool_inventory()
        assert inventory["source"] == "toolchest.catalog.load_inventory"
        assert inventory["total"] > 100

    def test_export_carries_the_measured_inventory(self, engine):
        engine.assert_belief("svc.port", "value", "8080", known_at=T1)
        exported = engine.export()
        assert exported["estate"]["inventory"]["total"] > 100
        assert exported["estate"]["identity"]["store_path"] == \
            os.environ["MEM20_STORE_PATH"]


# -- the MCP surface is reached through the real server -------------------

class TestMcpRegistration:
    """The subsystem must be reachable through the estate's MCP surface.

    A tools file that is imported by nobody, or listed but never dispatched, is
    the same decorative failure as an unused import - one level up. These tests
    build the real server object and call the tools through its real dispatcher.
    """

    @pytest.fixture()
    def tools_module(self):
        """Import ``mcp/tools/temporal_tools.py`` from the repo root."""
        mcp_tools = estate.REPO_ROOT / "mcp" / "tools"
        if not (mcp_tools / "temporal_tools.py").is_file():
            pytest.skip("mcp/tools/temporal_tools.py not present")
        if str(mcp_tools) not in sys.path:
            sys.path.insert(0, str(mcp_tools))
        import importlib

        return importlib.import_module("temporal_tools")

    def test_five_tools_are_declared(self, tools_module):
        names = [t["name"] for t in tools_module.TOOLS]
        assert names == ["temporal_put", "temporal_get", "temporal_slices",
                         "temporal_ingest", "temporal_doctor"]

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

    def test_a_tool_round_trips_through_handle(self, tools_module):
        out = tools_module.handle("temporal_put", {
            "subject": "svc.port", "attribute": "value", "value_ref": "8080",
            "known_at": T1})
        assert out["ok"] is True
        got = tools_module.handle("temporal_get", {"subject": "svc.port"})
        assert got["found"] is True
        assert got["values"] == ["8080"]

    def test_the_mcp_tool_refuses_a_credential_too(self, tools_module):
        with pytest.raises(Exception, match="credential|append-only|refusing"):
            tools_module.handle("temporal_put", {
                "subject": "svc.creds", "attribute": "TOKEN", "value_ref": "x"})


class TestWiringIsNotDecorative:
    """Static proof that each imported symbol is called in a non-test module."""

    PKG = Path(estate.__file__).resolve().parent

    @pytest.mark.parametrize("module, symbol", [
        ("estate_calls.py", "_validate_event_time"),
        ("estate_calls.py", "_ledger_load"),
        ("estate_calls.py", "_integrity_check"),
        ("estate_calls.py", "_identity_check"),
        ("estate_calls.py", "_classify_secret_value"),
        ("estate_calls.py", "_check_prohibited_uses"),
        ("estate_surface.py", "_classify_wire_line"),
        ("estate_surface.py", "_load_inventory"),
    ])
    def test_each_estate_symbol_is_called(self, module, symbol):
        """The alias must be resolved through ``need`` and then *invoked*.

        Each seam module binds its project's callable to a private alias and
        calls it as ``need(alias, ...)(args)``. Both halves matter: ``need``
        alone would only pass the callable around, and an alias never passed to
        ``need`` would be decorative. ``test_consumer_modules_call_the_seam``
        below asserts the seam functions themselves are reached from the engine
        and the adapter.
        """
        seam = (self.PKG / module).read_text(encoding="utf-8")
        assert f"need({symbol}," in seam, (
            f"{symbol} is imported but flows into no call - decorative import")

    @pytest.mark.parametrize("consumer, symbol, owner", [
        ("engine.py", "identity(", "estate_calls"),
        ("engine.py", "check_belief_legality(", "estate_calls"),
        ("engine.py", "classify_secret(", "estate_calls"),
        ("engine.py", "validate_event_time(", "estate_calls"),
        ("engine.py", "tool_inventory(", "estate_surface"),
        ("ledger_adapter.py", "verify_ledger_integrity(", "estate_calls"),
        ("ledger_adapter.py", "ledger_rows(", "estate_calls"),
        ("ledger_adapter.py", "is_noise_line(", "estate_surface"),
    ])
    def test_consumer_modules_call_the_seam(self, consumer, symbol, owner):
        """The consumer must both import the seam function and call it."""
        text = (self.PKG / consumer).read_text(encoding="utf-8")
        assert f"from .{owner} import" in text, (
            f"{consumer} does not import from {owner}")
        assert symbol in text, f"{consumer} does not call {symbol}"

    def test_no_estate_import_is_annotated_as_unused(self):
        """A ``# noqa: F401`` on an estate import is the decorative pattern.

        Exempt: an import inside a function that is deliberately deferred (the
        ``# noqa: PLC0415`` ones), because that is a load-ordering choice, not a
        claim that the name is unused - those names are called on the next line.
        """
        for name in ("estate.py", "engine.py", "ledger_adapter.py"):
            text = (self.PKG / name).read_text(encoding="utf-8")
            for line in text.splitlines():
                stripped = line.strip()
                if not stripped.startswith(("from . import", "from mem20")):
                    continue
                if "PLC0415" in line:
                    continue
                assert "F401" not in line and "noqa" not in line, (
                    f"decorative import in {name}: {stripped}")
