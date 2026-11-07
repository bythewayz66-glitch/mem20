"""Edge-to-cloud intelligence continuum domain model.

The continuum answers: *given this workload, which tier and target can run it
now with acceptable latency, cost and privacy, and how do we move it if that
target degrades?* "Invisible" placement means the caller states constraints, not
machines. "Resilient" means a failed or degraded target produces an explicit
migration/failover plan. "Cost-aware" means price and transport are first-class,
not an afterthought.

Tiers, in increasing distance from the caller:
    local -> edge -> private -> peer -> cloud

Everything here is pure: no I/O, no clock reads unless ``now`` is passed, no
imports from sibling subsystems. The service owns persistence and the ecosystem
seam owns cross-subsystem judgements.
"""
from __future__ import annotations

import math
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence

__all__ = [
    "Tier",
    "TargetStatus",
    "WorkloadState",
    "MigrationState",
    "Target",
    "Workload",
    "PlacementScore",
    "PlacementDecision",
    "MigrationPlan",
    "ContinuumHealth",
    "validate_tier",
    "capability_match",
    "estimate_execution_cost",
    "estimate_transport_cost",
    "estimate_latency",
    "privacy_ok",
    "score_target",
    "place_workload",
    "failover_plan",
    "migration_plan",
    "continuum_health",
]


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if value < lo else hi if value > hi else value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


class Tier(str, Enum):
    LOCAL = "local"
    EDGE = "edge"
    PRIVATE = "private"
    PEER = "peer"
    CLOUD = "cloud"


_TIER_DISTANCE = {
    Tier.LOCAL: 0.0,
    Tier.EDGE: 1.0,
    Tier.PRIVATE: 2.0,
    Tier.PEER: 2.5,
    Tier.CLOUD: 4.0,
}


class TargetStatus(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    DRAINING = "draining"
    OFFLINE = "offline"


class WorkloadState(str, Enum):
    QUEUED = "queued"
    PLACED = "placed"
    RUNNING = "running"
    MIGRATING = "migrating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MigrationState(str, Enum):
    PLANNED = "planned"
    VERIFYING = "verifying"
    CUTOVER = "cutover"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass(slots=True)
class Target:
    target_id: str
    name: str = ""
    tier: Tier = Tier.EDGE
    capabilities: frozenset[str] = field(default_factory=frozenset)
    cpu: float = 4.0
    memory_gb: float = 8.0
    latency_ms: float = 20.0
    bandwidth_mbps: float = 100.0
    cost_per_cpu_hour: float = 0.0
    egress_cost_per_gb: float = 0.0
    reliability: float = 0.99
    privacy_zones: frozenset[str] = field(default_factory=lambda: frozenset({"public"}))
    region: str = "default"
    status: TargetStatus = TargetStatus.ONLINE
    used_cpu: float = 0.0
    used_memory_gb: float = 0.0
    queue_depth: int = 0
    version: int = 0
    updated_at: float = 0.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.target_id = str(self.target_id).strip()
        _require(self.target_id, "target_id is required")
        if isinstance(self.tier, str):
            self.tier = Tier(self.tier)
        if isinstance(self.status, str):
            self.status = TargetStatus(self.status)
        self.capabilities = frozenset(str(c) for c in self.capabilities)
        self.privacy_zones = frozenset(str(z) for z in self.privacy_zones) or frozenset({"public"})
        _require(self.cpu > 0, "cpu must be > 0")
        _require(self.memory_gb > 0, "memory_gb must be > 0")
        _require(self.latency_ms >= 0, "latency_ms must be >= 0")
        _require(self.bandwidth_mbps > 0, "bandwidth_mbps must be > 0")
        _require(self.cost_per_cpu_hour >= 0, "cost_per_cpu_hour must be >= 0")
        _require(self.egress_cost_per_gb >= 0, "egress_cost_per_gb must be >= 0")
        _require(0.0 <= self.reliability <= 1.0, "reliability must be in [0, 1]")
        _require(self.used_cpu >= 0, "used_cpu must be >= 0")
        _require(self.used_memory_gb >= 0, "used_memory_gb must be >= 0")
        _require(self.queue_depth >= 0, "queue_depth must be >= 0")

    @property
    def free_cpu(self) -> float:
        return max(0.0, self.cpu - self.used_cpu)

    @property
    def free_memory_gb(self) -> float:
        return max(0.0, self.memory_gb - self.used_memory_gb)

    @property
    def load_fraction(self) -> float:
        return _clamp(max(self.used_cpu / self.cpu, self.used_memory_gb / self.memory_gb))

    @property
    def available(self) -> bool:
        return self.status in (TargetStatus.ONLINE, TargetStatus.DEGRADED)

    def reserve(self, workload: "Workload") -> None:
        self.used_cpu += float(workload.cpu)
        self.used_memory_gb += float(workload.memory_gb)
        self.queue_depth += 1

    def release(self, workload: "Workload") -> None:
        self.used_cpu = max(0.0, self.used_cpu - float(workload.cpu))
        self.used_memory_gb = max(0.0, self.used_memory_gb - float(workload.memory_gb))
        self.queue_depth = max(0, self.queue_depth - 1)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["tier"] = self.tier.value
        data["status"] = self.status.value
        data["capabilities"] = sorted(self.capabilities)
        data["privacy_zones"] = sorted(self.privacy_zones)
        return data

    @classmethod
    def from_dict(cls, data: Mapping) -> "Target":
        values = dict(data)
        values["capabilities"] = frozenset(values.get("capabilities") or ())
        values["privacy_zones"] = frozenset(values.get("privacy_zones") or ("public",))
        values["metadata"] = dict(values.get("metadata") or {})
        return cls(**{k: v for k, v in values.items() if k in cls.__dataclass_fields__})


@dataclass(slots=True)
class Workload:
    workload_id: str
    name: str = ""
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    cpu: float = 1.0
    memory_gb: float = 1.0
    size_mb: float = 10.0
    duration_s: float = 60.0
    max_latency_ms: float | None = None
    max_cost: float | None = None
    privacy_zone: str = "public"
    preferred_tiers: list[str] = field(default_factory=list)
    resilience: str = "standard"  # standard|high|critical
    priority: int = 50
    state: WorkloadState = WorkloadState.QUEUED
    assigned_target: str | None = None
    attempts: int = 0
    max_attempts: int = 3
    version: int = 0
    submitted_at: float = 0.0
    updated_at: float = 0.0
    idempotency_key: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.workload_id = str(self.workload_id).strip()
        _require(self.workload_id, "workload_id is required")
        if isinstance(self.state, str):
            self.state = WorkloadState(self.state)
        self.required_capabilities = frozenset(str(c) for c in self.required_capabilities)
        self.preferred_tiers = [str(t) for t in self.preferred_tiers]
        _require(self.cpu > 0, "cpu must be > 0")
        _require(self.memory_gb > 0, "memory_gb must be > 0")
        _require(self.size_mb >= 0, "size_mb must be >= 0")
        _require(self.duration_s > 0, "duration_s must be > 0")
        _require(0 <= self.priority <= 100, "priority must be 0..100")
        _require(self.max_attempts >= 0, "max_attempts must be >= 0")
        if self.max_latency_ms is not None:
            _require(self.max_latency_ms >= 0, "max_latency_ms must be >= 0")
        if self.max_cost is not None:
            _require(self.max_cost >= 0, "max_cost must be >= 0")
        _require(self.resilience in ("standard", "high", "critical"), "invalid resilience")

    def to_dict(self) -> dict:
        data = asdict(self)
        data["state"] = self.state.value
        data["required_capabilities"] = sorted(self.required_capabilities)
        return data

    @classmethod
    def from_dict(cls, data: Mapping) -> "Workload":
        values = dict(data)
        values["required_capabilities"] = frozenset(values.get("required_capabilities") or ())
        values["preferred_tiers"] = list(values.get("preferred_tiers") or [])
        values["metadata"] = dict(values.get("metadata") or {})
        return cls(**{k: v for k, v in values.items() if k in cls.__dataclass_fields__})


@dataclass(slots=True)
class PlacementScore:
    target_id: str
    tier: str
    total: float
    confidence: float
    feasible: bool
    components: dict
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class PlacementDecision:
    workload_id: str
    chosen: str | None
    score: float
    confidence: float
    alternatives: list[dict]
    bottlenecks: list[str]
    explanation: dict

    @property
    def placed(self) -> bool:
        return self.chosen is not None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class MigrationPlan:
    migration_id: str
    workload_id: str
    source: str | None
    destination: str | None
    state: MigrationState
    reason: str
    steps: list[dict]
    verified: bool = False
    rollback_safe: bool = True

    def to_dict(self) -> dict:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass(slots=True)
class ContinuumHealth:
    targets: int
    online: int
    degraded: int
    offline: int
    tiers: dict
    queued: int
    running: int
    migrating: int
    failed: int
    cpu_utilisation: float
    health: float

    def to_dict(self) -> dict:
        return asdict(self)


def validate_tier(value: str) -> Tier:
    try:
        return Tier(str(value))
    except ValueError as exc:
        raise ValueError(f"unknown tier {value!r}; expected one of {[t.value for t in Tier]}") from exc


def capability_match(target: Target, workload: Workload) -> tuple[bool, list[str]]:
    missing = sorted(workload.required_capabilities - target.capabilities)
    return (not missing, missing)


def estimate_execution_cost(target: Target, workload: Workload) -> float:
    hours = workload.duration_s / 3600.0
    return target.cost_per_cpu_hour * workload.cpu * hours


def estimate_transport_cost(target: Target, workload: Workload) -> float:
    gb = workload.size_mb / 1024.0
    return target.egress_cost_per_gb * gb


def estimate_latency(target: Target, workload: Workload) -> float:
    # base target latency + transfer time + queue penalty
    transfer_ms = (workload.size_mb * 8.0 / max(0.001, target.bandwidth_mbps)) * 1000.0
    queue_ms = target.queue_depth * 25.0
    return target.latency_ms + transfer_ms + queue_ms


def privacy_ok(target: Target, workload: Workload) -> bool:
    zone = workload.privacy_zone
    if zone in ("public", "", None):
        return True
    return zone in target.privacy_zones


def _tier_preference_bonus(target: Target, workload: Workload) -> float:
    if not workload.preferred_tiers:
        # invisible/cost-aware default: prefer closer tiers, but do not hardcode
        dist = _TIER_DISTANCE.get(target.tier, 4.0)
        return _clamp(1.0 - dist / 5.0)
    try:
        idx = workload.preferred_tiers.index(target.tier.value)
    except ValueError:
        return 0.2
    return _clamp(1.0 - idx / max(1, len(workload.preferred_tiers)))


_WEIGHTS = {
    "capability": 0.24,
    "latency": 0.18,
    "cost": 0.18,
    "reliability": 0.14,
    "capacity": 0.12,
    "privacy": 0.08,
    "preference": 0.06,
}


def score_target(target: Target, workload: Workload, *, now: float | None = None) -> PlacementScore:
    reasons: list[str] = []
    feasible = True

    if not target.available:
        feasible = False
        reasons.append(f"target status {target.status.value}")
    cap_ok, missing = capability_match(target, workload)
    if not cap_ok:
        feasible = False
        reasons.append(f"missing capabilities {','.join(missing)}")
    if target.free_cpu < workload.cpu or target.free_memory_gb < workload.memory_gb:
        feasible = False
        reasons.append(
            f"insufficient capacity cpu {target.free_cpu:.2f}/{workload.cpu} "
            f"mem {target.free_memory_gb:.2f}/{workload.memory_gb}GB"
        )
    if not privacy_ok(target, workload):
        feasible = False
        reasons.append(f"privacy zone {workload.privacy_zone!r} not allowed")
    latency = estimate_latency(target, workload)
    cost = estimate_execution_cost(target, workload) + estimate_transport_cost(target, workload)
    if workload.max_latency_ms is not None and latency > workload.max_latency_ms:
        feasible = False
        reasons.append(f"latency {latency:.1f}ms exceeds {workload.max_latency_ms}ms")
    if workload.max_cost is not None and cost > workload.max_cost:
        feasible = False
        reasons.append(f"cost {cost:.4f} exceeds {workload.max_cost}")

    latency_score = 1.0
    if workload.max_latency_ms:
        latency_score = _clamp(1.0 - latency / max(1.0, workload.max_latency_ms))
    else:
        latency_score = _clamp(1.0 - latency / 2000.0)
    cost_score = 1.0
    if workload.max_cost:
        cost_score = _clamp(1.0 - cost / max(1e-9, workload.max_cost))
    else:
        cost_score = _clamp(1.0 - cost / 10.0)
    cap_score = 1.0 if cap_ok else _clamp(1.0 - len(missing) / max(1, len(workload.required_capabilities)))
    capacity_score = _clamp(min(target.free_cpu / max(1e-9, workload.cpu),
                                target.free_memory_gb / max(1e-9, workload.memory_gb)) / 4.0)
    reliability = _clamp(target.reliability - 0.03 * target.queue_depth)
    pref = _tier_preference_bonus(target, workload)

    components = {
        "capability": cap_score,
        "latency": latency_score,
        "cost": cost_score,
        "reliability": reliability,
        "capacity": capacity_score,
        "privacy": 1.0 if privacy_ok(target, workload) else 0.0,
        "preference": pref,
    }
    total = sum(_WEIGHTS[k] * components[k] for k in _WEIGHTS)
    # resilience classes penalize low-reliability tiers for critical work
    if workload.resilience == "high":
        total *= _clamp(0.6 + 0.4 * reliability)
    elif workload.resilience == "critical":
        total *= _clamp(0.4 + 0.6 * reliability)
    total = _clamp(total)
    confidence = _clamp(0.35 + 0.65 * (total if feasible else total * 0.3))
    return PlacementScore(
        target_id=target.target_id, tier=target.tier.value, total=round(total, 6),
        confidence=round(confidence, 6), feasible=feasible,
        components={k: round(v, 6) for k, v in components.items()},
        reasons=reasons,
    )


def place_workload(targets: Sequence[Target], workload: Workload, *,
                   bonuses: Mapping[str, float] | None = None,
                   now: float | None = None) -> PlacementDecision:
    bonuses = bonuses or {}
    scored = []
    bottlenecks: list[str] = []
    for target in targets:
        score = score_target(target, workload, now=now)
        bonus = float(bonuses.get(target.target_id, 0.0))
        if score.feasible and bonus:
            score.total = round(_clamp(score.total + bonus), 6)
            score.components["cross_system_bonus"] = round(bonus, 6)
            score.confidence = round(_clamp(score.confidence + bonus * 0.3), 6)
        scored.append(score)
        if not score.feasible:
            bottlenecks.append(f"{target.target_id}: {'; '.join(score.reasons) or 'infeasible'}")
    feasible = [s for s in scored if s.feasible]
    feasible.sort(key=lambda s: (-s.total, -s.confidence, s.target_id))
    alternatives = [s.to_dict() for s in feasible[1:4]]
    explanation = {
        "evaluated": len(scored),
        "feasible": len(feasible),
        "weights": dict(_WEIGHTS),
        "resilience": workload.resilience,
    }
    if not feasible:
        return PlacementDecision(
            workload_id=workload.workload_id, chosen=None, score=0.0, confidence=0.0,
            alternatives=[], bottlenecks=bottlenecks or ["no targets available"],
            explanation=explanation,
        )
    best = feasible[0]
    explanation["chosen_components"] = best.components
    explanation["runner_up"] = alternatives[0]["target_id"] if alternatives else None
    return PlacementDecision(
        workload_id=workload.workload_id, chosen=best.target_id, score=best.total,
        confidence=best.confidence, alternatives=alternatives, bottlenecks=bottlenecks,
        explanation=explanation,
    )


def failover_plan(targets: Sequence[Target], workload: Workload, source_target_id: str | None,
                  reason: str = "source unavailable") -> MigrationPlan:
    candidates = [t for t in targets if t.target_id != source_target_id]
    decision = place_workload(candidates, workload)
    migration_id = f"mig-{uuid.uuid4().hex[:12]}"
    if decision.chosen is None:
        return MigrationPlan(
            migration_id=migration_id, workload_id=workload.workload_id,
            source=source_target_id, destination=None, state=MigrationState.FAILED,
            reason=reason, steps=[{"step": "select_destination", "ok": False,
                                   "bottlenecks": decision.bottlenecks}],
            verified=False, rollback_safe=True,
        )
    dest = decision.chosen
    steps = [
        {"step": "select_destination", "ok": True, "target": dest, "score": decision.score},
        {"step": "reserve_capacity", "ok": True, "target": dest},
        {"step": "transfer_state", "ok": True, "mode": "dual-write-then-verify",
         "size_mb": workload.size_mb},
        {"step": "verify_parity", "ok": True, "policy": "refuse_unverified_cutover"},
        {"step": "cutover", "ok": True, "from": source_target_id, "to": dest},
        {"step": "drain_source", "ok": bool(source_target_id), "target": source_target_id},
    ]
    return MigrationPlan(
        migration_id=migration_id, workload_id=workload.workload_id,
        source=source_target_id, destination=dest, state=MigrationState.PLANNED,
        reason=reason, steps=steps, verified=False, rollback_safe=True,
    )


def migration_plan(targets: Sequence[Target], workloads: Sequence[Workload],
                   *, load_threshold: float = 0.85) -> dict:
    by_id = {t.target_id: t for t in targets}
    moves = []
    for workload in workloads:
        if workload.state not in (WorkloadState.PLACED, WorkloadState.RUNNING):
            continue
        src = by_id.get(workload.assigned_target) if workload.assigned_target else None
        if src is None:
            continue
        if src.status in (TargetStatus.OFFLINE, TargetStatus.DRAINING) or src.load_fraction >= load_threshold:
            plan = failover_plan(targets, workload, src.target_id,
                                 reason=f"source {src.status.value} load={src.load_fraction:.2f}")
            moves.append(plan.to_dict())
    return {"moves": moves, "count": len(moves), "threshold": load_threshold}


def continuum_health(targets: Sequence[Target], workloads: Sequence[Workload] | None = None) -> ContinuumHealth:
    workloads = list(workloads or [])
    by_tier: dict[str, dict] = {}
    for t in Tier:
        tier_targets = [x for x in targets if x.tier == t]
        by_tier[t.value] = {
            "targets": len(tier_targets),
            "online": sum(1 for x in tier_targets if x.status == TargetStatus.ONLINE),
            "cpu": sum(x.cpu for x in tier_targets),
            "used_cpu": sum(x.used_cpu for x in tier_targets),
        }
    online = sum(1 for t in targets if t.status == TargetStatus.ONLINE)
    degraded = sum(1 for t in targets if t.status == TargetStatus.DEGRADED)
    offline = sum(1 for t in targets if t.status == TargetStatus.OFFLINE)
    cpu_cap = sum(t.cpu for t in targets if t.available) or 1.0
    cpu_used = sum(t.used_cpu for t in targets if t.available)
    util = _clamp(cpu_used / cpu_cap)
    queued = sum(1 for w in workloads if w.state == WorkloadState.QUEUED)
    running = sum(1 for w in workloads if w.state in (WorkloadState.PLACED, WorkloadState.RUNNING))
    migrating = sum(1 for w in workloads if w.state == WorkloadState.MIGRATING)
    failed = sum(1 for w in workloads if w.state == WorkloadState.FAILED)
    avail = online / max(1, len(targets)) if targets else 0.0
    work_ok = 1.0 - (failed / max(1, len(workloads))) if workloads else 1.0
    health = _clamp(0.45 * avail + 0.25 * (1.0 - degraded / max(1, len(targets) or 1))
                    + 0.20 * work_ok + 0.10 * (1.0 - util * 0.5))
    return ContinuumHealth(
        targets=len(targets), online=online, degraded=degraded, offline=offline,
        tiers=by_tier, queued=queued, running=running, migrating=migrating, failed=failed,
        cpu_utilisation=round(util, 6), health=round(health, 6),
    )
