from __future__ import annotations

from mem20edgetocloudintelligencecontinuumz.domain import (
    MigrationPlan, MigrationState, PlacementDecision, Target, Tier, Workload, WorkloadState,
)
from mem20edgetocloudintelligencecontinuumz.store import ContinuumStore, ConflictError, NotFoundError


def test_target_versioning_and_conflict(tmp_path):
    s = ContinuumStore(tmp_path / "c.db")
    t = Target(target_id="t1", tier=Tier.EDGE, capabilities={"compute"}, cpu=4, memory_gb=8)
    r1 = s.put_target(t)
    assert r1["version"] == 1
    r2 = s.put_target(s.get_target("t1"))
    assert r2["version"] == 2
    try:
        s.put_target(t, expected_version=1)
        raise AssertionError("expected conflict")
    except ConflictError:
        pass
    assert s.get_target("t1").version == 2
    assert len(s.list_targets()) == 1
    s.delete_target("t1")
    try:
        s.get_target("nope") or s.require_target("nope")
        raise AssertionError("expected not found")
    except NotFoundError:
        pass


def test_workload_idempotency_and_events(tmp_path):
    s = ContinuumStore(tmp_path / "c.db")
    s.idempotency_store("k1", "w1")
    assert s.idempotency_lookup("k1") == "w1"
    assert s.idempotency_lookup("missing") is None
    w = Workload(workload_id="w1", cpu=1, memory_gb=1)
    s.put_workload(w)
    w.state = WorkloadState.RUNNING
    s.put_workload(w)
    got = s.get_workload("w1")
    assert got.state == WorkloadState.RUNNING and got.version == 2
    evs = s.events_since(0, 50)
    assert any(e["kind"] == "workload.upserted" for e in evs)
    metrics = s.metrics()
    assert metrics["workloads"] == 1 and metrics["events"] >= 1


def test_placement_migration_snapshot_restore(tmp_path):
    s = ContinuumStore(tmp_path / "c.db")
    s.put_target(Target(target_id="t1", tier=Tier.LOCAL, capabilities={"compute"}, cpu=4, memory_gb=8))
    s.put_workload(Workload(workload_id="w1", cpu=1, memory_gb=1))
    pid = s.record_placement(PlacementDecision(workload_id="w1", chosen="t1", score=0.9, confidence=0.8, alternatives=[], bottlenecks=[], explanation={}))
    assert pid
    assert s.list_placements("w1")[0]["chosen"] == "t1"
    plan = MigrationPlan(migration_id="m1", workload_id="w1", source="t1", destination="t1", state=MigrationState.PLANNED, reason="test", steps=[])
    s.put_migration(plan)
    assert s.list_migrations()[0]["migration_id"] == "m1"
    snap = s.snapshot("before")
    s.delete_target("t1")
    assert s.list_targets() == []
    restored = s.restore(snap["snapshot_id"])
    assert restored["targets"] == 1
    assert s.get_target("t1") is not None
