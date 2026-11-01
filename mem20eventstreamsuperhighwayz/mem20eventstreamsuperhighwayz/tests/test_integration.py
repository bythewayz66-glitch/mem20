"""Integration tests: every cross-module call is exercised, not just imported.

Each test drives a real mem20 project API through the superhighway's seam and
asserts on the real value that came back. The store is isolated per test via
``MEM20_STORE_PATH`` so the suite never touches a live ledger.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

PKG = "mem20eventstreamsuperhighwayz"


@pytest.fixture()
def store(tmp_path, monkeypatch):
    """Point the memory engine at a throwaway store for this test.

    The engine reads ``STORE_DIR`` at import time, so the module has to be
    re-imported after the env var is set. Popping ``sys.modules`` alone is not
    enough: the parent package keeps its own attribute pointing at the old
    module object, and ``import memory_engine.memory`` then hands that stale
    object back without re-registering it — which makes a later
    ``importlib.reload`` fail with "module not in sys.modules". The attribute
    is cleared too.
    """
    path = str(tmp_path / "store")
    monkeypatch.setenv("MEM20_STORE_PATH", path)
    _reset_engine()
    yield path
    _reset_engine()


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
def gateway_home(tmp_path, monkeypatch):
    """Keep gateway writes out of the real /opt/mem20 tree."""
    import importlib

    from mem20eventstreamsuperhighwayz import _bootstrap

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
    from mem20eventstreamsuperhighwayz import _bootstrap

    added = _bootstrap.ensure_estate_path()
    assert isinstance(added, list)
    # idempotent: a second call adds nothing new
    assert _bootstrap.ensure_estate_path() == []
    assert Path(_bootstrap.REPO_ROOT).is_dir()


# ------------------------------------------------------- memory_engine (1)


def test_remember_event_persists_a_real_ledger_row(store):
    integ, dom = _integration(), _domain()
    stream = dom.create_stream("orders")
    event = dom.publish(stream, "order.created", {"id": 7}, key="o-7")

    record = integ.remember_event(stream, event)

    assert record["topic"] == "eventstream.orders.order.created"
    assert record["epistemic_status"] == "observed"
    ledger = Path(store) / "ledger.jsonl"
    assert ledger.is_file()
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    assert any(r["id"] == record["id"] for r in rows)


def test_recall_events_returns_what_was_persisted(store):
    integ, dom = _integration(), _domain()
    stream = dom.create_stream("orders")
    integ.remember_event(stream, dom.publish(stream, "order.created", {"id": 1}))
    integ.remember_event(stream, dom.publish(stream, "order.created", {"id": 2}))

    rows = integ.recall_events("orders", "order.created")

    assert len(rows) == 2
    payloads = sorted(json.loads(r["content"])["payload"]["id"] for r in rows)
    assert payloads == [1, 2]


def test_memory_status_reports_the_isolated_store(store):
    integ = _integration()
    text = integ.memory_status()
    assert "ledger events" in text


# ------------------------------------------- memory_engine.retrieval_v2 (2)


def test_search_events_decomposes_a_compound_question(store):
    integ = _integration()
    result = integ.search_events("what is the p95 latency and which partition is hot", k=3)
    assert result["parts"] == ["what is the p95 latency", "which partition is hot"]
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
    stream = dom.create_stream("orders")
    event = dom.publish(stream, "order.created", {"id": 9}, key="o-9")

    entry = integ.announce(stream, event)

    assert entry["agent_name"] == "eventstream-orders"
    assert entry["target"] == "eventstream"
    assert "order.created" in entry["message"]
    assert gateway_home.MESSAGES_FILE.is_file()
    assert "eventstream-orders" in gateway_home.load_names()


def test_fleet_messages_reads_back_the_announcement(store, gateway_home):
    integ, dom = _integration(), _domain()
    stream = dom.create_stream("orders")
    integ.announce(stream, dom.publish(stream, "order.created", {"id": 3}))

    messages = integ.fleet_messages(limit=5)

    assert len(messages) == 1
    assert messages[0]["message"].startswith("order.created")


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


def test_publish_and_persist_runs_the_whole_seam(store, gateway_home):
    integ, dom = _integration(), _domain()
    stream = dom.create_stream("orders")

    out = integ.publish_and_persist(stream, "order.created", {"id": 11}, key="o-11")

    assert out["event"]["seq"] == 1
    assert out["memory_topic"] == "eventstream.orders.order.created"
    assert out["announced"]["agent_name"] == "eventstream-orders"
    assert len(integ.recall_events("orders")) == 1


def test_stream_report_combines_domain_and_substrate(store):
    integ, dom = _integration(), _domain()
    stream = dom.create_stream("orders")
    dom.publish(stream, "order.created", {"id": 1})
    dom.subscribe(stream, "billing")

    report = integ.stream_report(stream)

    assert report["stream"] == "orders"
    assert report["events"] == 1
    assert report["subscribers"] == ["billing"]
    assert report["lag"] == {"billing": 1}
    assert report["inventory"]["total"] > 0
