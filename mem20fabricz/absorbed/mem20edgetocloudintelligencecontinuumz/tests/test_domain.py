from __future__ import annotations

from mem20edgetocloudintelligencecontinuumz import domain
from mem20edgetocloudintelligencecontinuumz.domain import (
    MigrationState, PlacementDecision, Target, TargetStatus, Tier, Workload, WorkloadState,
    capability_match, continuum_health, estimate_latency, failover_plan, place_workload,
    privacy_ok, score_target,
)


def mk_target(tid="t1", **kw):
    base = dict(target_id=tid, tier=Tier.EDGE, capabilities={"compute"}, cpu=8, memory_gb=16,
                latency_ms=20, bandwidth_mbps=100, cost_per_cpu_hour=0.05, reliability=0.99,
                privacy_zones={"public", "internal"}, status=TargetStatus.ONLINE)
    base.update(kw)
    return Target(**base)


def mk_work(tid="w1", **kw):
    base = dict(workload_id=tid, required_capabilities={"compute"}, cpu=2, memory_gb=2,
                size_mb=10, duration_s=60, priority=50, privacy_zone="public")
    base.update(kw)
    return Workload(**base)


def test_target_validation_and_capacity():
    t = mk_target()
    assert t.free_cpu == 8
    w = mk_work(cpu=3, memory_gb=4)
    t.reserve(w)
    assert t.used_cpu == 3 and t.queue_depth == 1
    assert t.free_memory_gb == 12
    t.release(w)
    assert t.free_cpu == 8 and t.queue_depth == 0
    try:
        Target(target_id="", cpu=1, memory_gb=1)
        raise AssertionError("expected")
    except ValueError:
        pass
    try:
        Target(target_id="x", cpu=-1, memory_gb=1)
        raise AssertionError("expected")
    except ValueError:
        pass


def test_tier_and_privacy_and_capability():
    assert domain.validate_tier("cloud") == Tier.CLOUD
    t = mk_target(capabilities={"compute", "gpu"}, privacy_zones={"public"})
    w = mk_work(required_capabilities={"compute"})
    ok, missing = capability_match(t, w)
    assert ok and missing == []
    ok, missing = capability_match(t, mk_work(required_capabilities={"tpu"}))
    assert not ok and missing == ["tpu"]
    assert privacy_ok(mk_target(privacy_zones={"public"}), mk_work(privacy_zone="public"))
    assert not privacy_ok(mk_target(privacy_zones={"public"}), mk_work(privacy_zone="secret"))


def test_latency_and_cost_estimates():
    t = mk_target(latency_ms=10, bandwidth_mbps=80, cost_per_cpu_hour=0.1)
    w = mk_work(size_mb=80, cpu=2, duration_s=3600)
    lat = estimate_latency(t, w)
    assert lat >= 10  # base + transfer
    cost = domain.estimate_execution_cost(t, w)
    assert abs(cost - 0.2) < 1e-9
    assert domain.estimate_transport_cost(t, w) >= 0


def test_scoring_prefers_feasible_lower_latency_cost():
    local = mk_target("local", tier=Tier.LOCAL, latency_ms=2, cost_per_cpu_hour=0.0, reliability=0.99, bandwidth_mbps=10000)
    cloud = mk_target("cloud", tier=Tier.CLOUD, latency_ms=120, cost_per_cpu_hour=0.5, reliability=0.999, bandwidth_mbps=10000)
    w = mk_work(size_mb=1, max_latency_ms=50)
    sl = score_target(local, w)
    sc = score_target(cloud, w)
    assert sl.feasible and not sc.feasible
    w2 = mk_work(size_mb=1)
    d = place_workload([cloud, local], w2)
    assert d.chosen == "local"
    assert d.confidence > 0


def test_scoring_rejects_capacity_privacy_capability():
    t = mk_target(cpu=1, memory_gb=1, capabilities={"cpu"}, privacy_zones={"public"})
    d = place_workload([t], mk_work(cpu=4))
    assert d.chosen is None and any("capacity" in b for b in d.bottlenecks)
    d = place_workload([t], mk_work(required_capabilities={"gpu"}))
    assert d.chosen is None and any("capabilities" in b for b in d.bottlenecks)
    d = place_workload([t], mk_work(privacy_zone="secret"))
    assert d.chosen is None and any("privacy" in b for b in d.bottlenecks)


def test_failover_plan_and_migration_plan():
    src = mk_target("src", tier=Tier.EDGE)
    dst = mk_target("dst", tier=Tier.CLOUD, latency_ms=80)
    w = mk_work()
    w.state = WorkloadState.RUNNING
    w.assigned_target = "src"
    plan = failover_plan([src, dst], w, "src", reason="outage")
    assert plan.destination == "dst"
    assert plan.rollback_safe and plan.state == MigrationState.PLANNED
    src.status = TargetStatus.OFFLINE
    mp = domain.migration_plan([src, dst], [w])
    assert mp["count"] == 1 and mp["moves"][0]["destination"] == "dst"


def test_continuum_health():
    targets = [mk_target("a", tier=Tier.LOCAL), mk_target("b", tier=Tier.CLOUD, status=TargetStatus.DEGRADED)]
    workloads = [mk_work("w1"), mk_work("w2")]
    workloads[0].state = WorkloadState.RUNNING
    workloads[1].state = WorkloadState.QUEUED
    h = continuum_health(targets, workloads)
    assert h.targets == 2 and h.online == 1 and h.degraded == 1
    assert h.running == 1 and h.queued == 1
    assert 0 <= h.health <= 1
    assert "local" in h.tiers and "cloud" in h.tiers
