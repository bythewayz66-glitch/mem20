"""State-plane tests: versions, journal, events, snapshots and idempotency.

The store is where an edge box loses power. Every test here is written against a
real SQLite file (``tmp_path``), never a fake connection, so a broken transaction
boundary or a forgotten WAL pragma fails the suite.
"""

from __future__ import annotations

import sqlite3

import pytest

from mem20edgefleetbrainz.domain import (
    Node,
    NodeStatus,
    PlacementDecision,
    Workload,
    WorkloadState,
)
from mem20edgefleetbrainz.store import ConflictError, FleetStore, NotFoundError


def make_node(node_id: str = "n1", **overrides) -> Node:
    values = dict(
        node_id=node_id,
        cpu_cores=8,
        memory_gb=16.0,
        capabilities=frozenset({"cpu"}),
        last_seen=1_000_000.0,
    )
    values.update(overrides)
    return Node(**values)


def make_workload(workload_id: str = "w1", **overrides) -> Workload:
    values = dict(workload_id=workload_id, cpu=2.0, memory_gb=2.0)
    values.update(overrides)
    return Workload(**values)


@pytest.fixture()
def store(tmp_path):
    return FleetStore(tmp_path / "fleet.db")


# ---------------------------------------------------------------------------
# schema and node lifecycle
# ---------------------------------------------------------------------------
def test_store_creates_wal_database(tmp_path):
    path = tmp_path / "nested" / "fleet.db"
    db = FleetStore(path)
    assert path.is_file()
    with sqlite3.connect(path) as raw:
        mode = raw.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"
    assert db.metrics()["nodes"] == 0


def test_node_versions_increment_and_conflict(store):
    first = store.put_node(make_node())
    assert first["version"] == 1
    assert store.node_version("n1") == 1

    second = store.put_node(make_node(status=NodeStatus.DRAINING))
    assert second["version"] == 2
    assert store.get_node("n1").status is NodeStatus.DRAINING

    with pytest.raises(ConflictError):
        store.put_node(make_node(), expected_version=1)
    with pytest.raises(ConflictError):
        store.delete_node("n1", expected_version=1)

    deleted = store.delete_node("n1", expected_version=2)
    assert deleted["deleted"] is True
    assert store.get_node("n1") is None
    with pytest.raises(NotFoundError):
        store.require_node("n1")


def test_nodes_list_is_sorted_and_round_trips_fields(store):
    store.put_node(make_node("zeta", capabilities={"cpu", "gpu"}, gpu_count=1))
    store.put_node(make_node("alpha", region="eu-west", latency_ms=120.0))
    nodes = store.list_nodes()
    assert [node.node_id for node in nodes] == ["alpha", "zeta"]
    assert nodes[0].region == "eu-west"
    assert nodes[1].capabilities == frozenset({"cpu", "gpu"})


def test_store_survives_a_new_instance(tmp_path):
    path = tmp_path / "fleet.db"
    FleetStore(path).put_node(make_node("persisted"))
    reopened = FleetStore(path)
    assert reopened.get_node("persisted").node_id == "persisted"


# ---------------------------------------------------------------------------
# workload lifecycle
# ---------------------------------------------------------------------------
def test_workload_versions_state_index_and_conflict(store):
    workload = make_workload()
    assert store.put_workload(workload)["version"] == 1
    assert [w.workload_id for w in store.list_workloads(WorkloadState.QUEUED)] == ["w1"]
    assert store.list_workloads("running") == []

    workload.state = WorkloadState.RUNNING
    workload.assigned_node = "n1"
    assert store.put_workload(workload)["version"] == 2
    running = store.list_workloads(WorkloadState.RUNNING)
    assert running[0].assigned_node == "n1"

    with pytest.raises(ConflictError):
        store.put_workload(workload, expected_version=1)
    with pytest.raises(NotFoundError):
        store.require_workload("missing")

    deleted = store.delete_workload("w1")
    assert deleted["deleted"] is True
    assert deleted["event_seq"] >= 1
    assert store.get_workload("w1") is None


# ---------------------------------------------------------------------------
# decision journal and event stream
# ---------------------------------------------------------------------------
def test_placement_journal_keeps_the_explanation(store):
    decision = PlacementDecision(
        workload_id="w1",
        chosen="n1",
        score=0.8125,
        confidence=0.77,
        alternatives=[{"node_id": "n2", "total": 0.7}],
        bottlenecks=["n2: cpu 1.0/4.0"],
        explanation={"feasible_nodes": 1},
    )
    seq = store.record_placement(decision)
    assert seq >= 1
    rows = store.list_placements()
    assert rows[0]["workload_id"] == "w1"
    assert rows[0]["chosen"] == "n1"
    assert rows[0]["explanation"]["feasible_nodes"] == 1
    assert rows[0]["bottlenecks"] == ["n2: cpu 1.0/4.0"]


def test_events_are_ordered_and_resumable(store):
    store.append_event("custom.one", {"value": 1})
    store.append_event("custom.two", {"value": 2, "wibble": object()})
    latest = store.latest_event_seq()
    assert latest == 2

    recent = store.events_since(1)
    assert [event["kind"] for event in recent] == ["custom.two"]
    assert recent[0]["payload"]["value"] == 2
    # default=str keeps a non-JSON value from breaking the stream
    assert isinstance(recent[0]["payload"]["wibble"], str)

    store.put_node(make_node())
    assert store.events_since(2)[0]["kind"] == "node.upserted"


# ---------------------------------------------------------------------------
# snapshots
# ---------------------------------------------------------------------------
def test_snapshot_restore_is_a_real_rollback(store):
    store.put_node(make_node("n1"))
    store.put_workload(make_workload("w1"))
    snap = store.snapshot("before")
    assert snap["nodes"] == 1
    assert snap["workloads"] == 1

    store.delete_node("n1")
    store.delete_workload("w1")
    assert store.list_nodes() == []

    restored = store.restore(snap["snapshot_id"])
    assert restored["nodes"] == 1
    assert restored["workloads"] == 1
    assert store.require_node("n1").node_id == "n1"
    assert store.require_workload("w1").workload_id == "w1"
    assert store.list_snapshots()[0]["label"] == "before"

    with pytest.raises(NotFoundError):
        store.restore("snap-does-not-exist")


def test_restore_resets_versions_so_concurrency_stays_honest(store):
    store.put_node(make_node("n1"))
    snap = store.snapshot()
    store.put_node(make_node("n1"))
    store.restore(snap["snapshot_id"])
    assert store.node_version("n1") == 1


# ---------------------------------------------------------------------------
# idempotency and metrics
# ---------------------------------------------------------------------------
def test_idempotency_keys_are_claimed_once(store):
    assert store.claim_key("submit:w1", "w1") is True
    assert store.claim_key("submit:w1", "w1") is False
    assert store.lookup_key("submit:w1") == "w1"
    assert store.lookup_key("missing") is None
    # an empty key is always claimable and never stored
    assert store.claim_key("", "w2") is True
    assert store.lookup_key("") is None


def test_metrics_count_every_shape(store):
    store.put_node(make_node("n1"))
    store.put_workload(make_workload("w1"))
    store.record_placement(PlacementDecision(
        workload_id="w1", chosen="n1", score=0.5, confidence=0.5))
    store.snapshot("m")
    metrics = store.metrics()
    assert metrics["store_path"].endswith("fleet.db")
    assert metrics["nodes"] == 1
    assert metrics["workloads"] == 1
    assert metrics["placements"] == 1
    assert metrics["snapshots"] == 1
    assert metrics["events"] >= 4
    assert metrics["latest_event_seq"] == metrics["events"]
