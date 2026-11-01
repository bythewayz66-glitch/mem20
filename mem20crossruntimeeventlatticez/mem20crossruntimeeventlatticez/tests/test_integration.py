"""Integration tests: every cross-module call is exercised, not just imported.

Each test drives a real mem20 project API through the lattice's seam and asserts
on the real value that came back. The store is isolated per test via
``MEM20_STORE_PATH`` so the suite never touches a live ledger.
"""
import json
import sys
from pathlib import Path

import pytest

PKG = "mem20crossruntimeeventlatticez"


def _reset_engine():
    import importlib

    for name in ("memory_engine.memory", "memory_engine.retrieval_v2", "memory"):
        sys.modules.pop(name, None)
    try:
        engine_pkg = importlib.import_module("memory_engine")
    except ImportError:
        return
    for attr in ("memory", "retrieval_v2"):
        if hasattr(engine_pkg, attr):
            delattr(engine_pkg, attr)


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Point the memory engine at a throwaway store for this test.

    The engine reads ``STORE_DIR`` at import time, so the module has to be
    re-imported after the env var is set. Popping ``sys.modules`` alone is not
    enough: the parent package keeps its own attribute pointing at the old
    module object, and ``import memory_engine.memory`` then hands that stale
    object back without re-registering it — which makes a later
    ``importlib.reload`` fail with "module not in sys.modules".
    """
    path = str(tmp_path / "store")
    monkeypatch.setenv("MEM20_STORE_PATH", path)
    _reset_engine()
    yield path
    _reset_engine()


@pytest.fixture()
def gateway_home(tmp_path, monkeypatch):
    """Keep gateway writes out of the real /opt/mem20 tree."""
    import importlib

    from mem20crossruntimeeventlatticez import _bootstrap

    _bootstrap.ensure_estate_path()
    gw = importlib.import_module("gateway.hermes_gateway")
    monkeypatch.setattr(gw, "GATEWAY_DIR", tmp_path / "gateway")
    monkeypatch.setattr(gw, "NAMES_FILE", tmp_path / "gateway" / "agent_names.json")
    monkeypatch.setattr(gw, "MESSAGES_FILE", tmp_path / "gateway" / "messages.jsonl")
    return gw


def _integration():
    import importlib

    return importlib.import_module(PKG + ".integration")


def _domain():
    import importlib

    return importlib.import_module(PKG + ".domain")


# ---------------------------------------------------------------- bootstrap


def test_bootstrap_puts_estate_on_path():
    from mem20crossruntimeeventlatticez import _bootstrap

    added = _bootstrap.ensure_estate_path()
    assert isinstance(added, list)
    assert _bootstrap.ensure_estate_path() == []
    assert Path(_bootstrap.REPO_ROOT).is_dir()


# ------------------------------------------------------- memory_engine (1)


def test_remember_event_persists_a_real_ledger_row(store):
    integ, dom = _integration(), _domain()
    event = dom.emit("click", {"x": 1}, source="edge")

    record = integ.remember_event(event, lattice="web")

    assert record["topic"] == "lattice.web.click"
    assert record["epistemic_status"] == "observed"
    ledger = Path(store) / "ledger.jsonl"
    assert ledger.is_file()
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    assert any(r["id"] == record["id"] for r in rows)


def test_remember_event_keeps_the_vector_clock(store):
    integ, dom = _integration(), _domain()
    parent = dom.emit("start", {}, source="local")
    child = dom.causal_link(parent, dom.emit("finish", {}, source="edge"))

    integ.remember_event(child, lattice="web")

    row = integ.recall_events("web", "finish")[0]
    body = json.loads(row["content"])
    assert body["parent"] == parent["id"]
    assert parent["id"] in body["vector"]


def test_recall_events_returns_what_was_persisted(store):
    integ, dom = _integration(), _domain()
    integ.remember_event(dom.emit("a", {"n": 1}), lattice="web")
    integ.remember_event(dom.emit("a", {"n": 2}), lattice="web")

    rows = integ.recall_events("web", "a")

    assert len(rows) == 2
    assert sorted(json.loads(r["content"])["payload"]["n"] for r in rows) == [1, 2]


def test_memory_status_reports_the_isolated_store(store):
    integ = _integration()
    assert "ledger events" in integ.memory_status()


# ------------------------------------------- memory_engine.retrieval_v2 (2)


def test_search_history_decomposes_a_compound_question(store):
    integ = _integration()
    result = integ.search_history(
        "which runtime emitted the first failure and what did it cause", k=3
    )
    assert result["parts"] == [
        "which runtime emitted the first failure",
        "what did it cause",
    ]
    assert "results" in result


# ------------------------------------------------------------ toolchest (3)


def test_capability_inventory_is_the_measured_inventory():
    integ = _integration()
    inv = integ.capability_inventory()
    assert inv["format_version"]
    assert inv["counts"]["subsystem"] > 0
    assert integ.inventory_counts()["total"] == inv["counts"]["total"]


# -------------------------------------------------------------- gateway (4)


def test_announce_writes_a_real_gateway_message(store, gateway_home):
    integ, dom = _integration(), _domain()
    event = dom.emit("click", {"x": 1}, source="edge")

    entry = integ.announce(event, lattice="web")

    assert entry["agent_name"] == "lattice-web"
    assert entry["target"] == "lattice"
    assert "click" in entry["message"]
    assert gateway_home.MESSAGES_FILE.is_file()
    assert "lattice-web" in gateway_home.load_names()


def test_fleet_messages_reads_back_the_announcement(store, gateway_home):
    integ, dom = _integration(), _domain()
    integ.announce(dom.emit("click", {}), lattice="web")

    messages = integ.fleet_messages(limit=5)

    assert len(messages) == 1
    assert messages[0]["message"].startswith("click")


# ----------------------------------------------------------- mem20verify (5)


def test_verify_memory_integrity_round_trips_the_engine(store):
    integ = _integration()
    report = integ.verify_memory_integrity()
    assert report["checked"] > 0
    assert report["roundtrip_ok"] == report["checked"]
    assert report["failures"] == []


# -------------------------------------------------------------- mem20ops (6)


def test_identity_report_reads_the_isolated_store(store):
    integ = _integration()
    report = integ.identity_report()
    assert report["store_path"] == store
    assert report["pinned_block_count"] == 0


# ------------------------------------------------------------ mem20corez (7)


def test_compact_payload_quantizes_with_measured_error():
    integ = _integration()
    out = integ.compact_payload([1.0, 2.0, 3.0, 4.0], bits=8)
    assert out["bits"] == 8
    assert out["shape"] == [4, 1]
    assert len(out["q"]) == 4
    assert out["max_abs_error"] < 0.05


# ------------------------------------------------------- the composed path


def test_emit_and_record_runs_the_whole_seam(store, gateway_home):
    integ = _integration()

    out = integ.emit_and_record("click", {"x": 1}, lattice="web", source="edge")

    assert out["event"]["source"] == "edge"
    assert out["memory_topic"] == "lattice.web.click"
    assert out["announced"]["agent_name"] == "lattice-web"
    assert len(integ.recall_events("web")) == 1


def test_emit_and_record_links_causality(store, gateway_home):
    integ, dom = _integration(), _domain()
    parent = dom.emit("start", {}, source="local")

    out = integ.emit_and_record("finish", {}, lattice="web", parent=parent)

    assert out["event"]["parent"] == parent["id"]
    assert parent["id"] in out["event"]["vector"]


def test_lattice_report_combines_domain_and_substrate(store):
    integ, dom = _integration(), _domain()
    a = dom.emit("click", {}, source="edge")
    b = dom.causal_link(a, dom.emit("view", {}, source="cloud"))

    report = integ.lattice_report([{"events": [a]}, {"events": [b]}], name="web")

    assert report["lattice"] == "web"
    assert report["count"] == 2
    assert report["by_type"] == {"click": 1, "view": 1}
    assert report["sources"] == ["cloud", "edge"]
    assert report["causal_links"] == 1
    assert report["inventory"]["total"] > 0
