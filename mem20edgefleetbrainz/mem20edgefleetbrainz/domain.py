"""Edge fleet brain domain model, placement scoring, energy and fault prediction.

The fleet brain answers one question continuously: *given this workload, which
of the heterogeneous machines that are actually reachable right now should run
it, and why?* A machine can be a rack server, a phone on a charger, a NAS
appliance, a laptop that wakes for a few hours, or an edge box behind a slow
uplink. Treating them as interchangeable "capacity" loses the only interesting
part of the problem, so this module keeps the differences explicit:

* capabilities are a hard gate - a phone cannot run a CUDA workload;
* energy is a first-class cost - the cheapest node is often the one already
  running warm, not the one with the most idle cores;
* reliability decays with uptime and heat - a node that has been up for a month
  at 80 C is a worse bet than a cold spare even if both report "online";
* latency and locality decide whether remote placement is worth it at all.

Everything here is pure: no I/O, no clock reads unless a caller passes ``now``,
no imports from sibling subsystems. The persistent state plane is
:mod:`mem20edgefleetbrainz.store` and the cross-subsystem seam is
:mod:`mem20edgefleetbrainz.ecosystem`.
"""
from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Sequence

__all__ = [
    "DeviceKind",
    "NodeStatus",
    "WorkloadState",
    "Node",
    "Workload",
    "PlacementScore",
    "PlacementDecision",
    "FaultForecast",
    "capability_match",
    "estimate_energy_wh",
    "estimate_cost",
    "fault_risk",
    "score_placement",
    "place_workload",
    "rebalance_plan",
    "evacuation_plan",
    "fleet_health",
    "energy_profile",
    "predict_fleet_faults",
]


class DeviceKind(str, Enum):
    """The physical classes of hardware the fleet can own."""

    SERVER = "server"
    LAPTOP = "laptop"
    PHONE = "phone"
    APPLIANCE = "appliance"
    EDGE_BOX = "edge_box"


class NodeStatus(str, Enum):
    """Lifecycle of a node as the scheduler sees it."""

    ONLINE = "online"
    DRAINING = "draining"
    DEGRADED = "degraded"
    SLEEPING = "sleeping"
    OFFLINE = "offline"


class WorkloadState(str, Enum):
    """Lifecycle of a workload."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EVICTED = "evicted"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


@dataclass
class Node:
    """A single heterogeneous machine.

    ``current_cpu``/``current_memory_gb`` are the *reserved* amounts, not a
    sampled utilisation: the scheduler owns the accounting so two placements
    cannot both believe the same core is free.
    """

    node_id: str
    kind: DeviceKind = DeviceKind.SERVER
    capabilities: frozenset[str] = field(default_factory=frozenset)
    cpu_cores: int = 4
    memory_gb: float = 8.0
    gpu_count: int = 0
    bandwidth_mbps: float = 100.0
    idle_watts: float = 12.0
    peak_watts: float = 65.0
    price_per_hour: float = 0.0
    reliability: float = 0.98
    latency_ms: float = 5.0
    region: str = "local"
    status: NodeStatus = NodeStatus.ONLINE
    current_cpu: float = 0.0
    current_memory_gb: float = 0.0
    last_seen: float = 0.0
    uptime_s: float = 0.0
    fault_count: int = 0
    temperature_c: float = 40.0

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("node_id required")
        if not isinstance(self.kind, DeviceKind):
            self.kind = DeviceKind(str(self.kind))
        if not isinstance(self.status, NodeStatus):
            self.status = NodeStatus(str(self.status))
        self.capabilities = frozenset(str(c) for c in self.capabilities)
        _require(self.cpu_cores > 0, "cpu_cores must be > 0")
        _require(self.memory_gb > 0, "memory_gb must be > 0")
        _require(self.peak_watts >= self.idle_watts >= 0, "watts must satisfy peak >= idle >= 0")
        _require(self.bandwidth_mbps > 0, "bandwidth_mbps must be > 0")
        _require(self.price_per_hour >= 0, "price_per_hour must be >= 0")
        _require(0.0 <= self.reliability <= 1.0, "reliability must be in [0, 1]")
        _require(self.latency_ms >= 0, "latency_ms must be >= 0")
        _require(self.current_cpu >= 0, "current_cpu must be >= 0")
        _require(self.current_memory_gb >= 0, "current_memory_gb must be >= 0")
        _require(self.fault_count >= 0, "fault_count must be >= 0")
        self.current_cpu = float(self.current_cpu)
        self.current_memory_gb = float(self.current_memory_gb)
        self.uptime_s = float(self.uptime_s)
        self.last_seen = float(self.last_seen)

    # -- accounting ---------------------------------------------------
    @property
    def free_cpu(self) -> float:
        return max(0.0, float(self.cpu_cores) - self.current_cpu)

    @property
    def free_memory_gb(self) -> float:
        return max(0.0, float(self.memory_gb) - self.current_memory_gb)

    @property
    def load_fraction(self) -> float:
        cpu = self.current_cpu / float(self.cpu_cores) if self.cpu_cores else 1.0
        mem = self.current_memory_gb / self.memory_gb if self.memory_gb else 1.0
        return _clamp(max(cpu, mem))

    def schedulable(self) -> bool:
        return self.status in (NodeStatus.ONLINE, NodeStatus.DEGRADED)

    def has_capabilities(self, required: Iterable[str]) -> bool:
        return set(required).issubset(self.capabilities)

    def reserve(self, workload: "Workload") -> None:
        self.current_cpu += float(workload.cpu)
        self.current_memory_gb += float(workload.memory_gb)

    def release(self, workload: "Workload") -> None:
        self.current_cpu = max(0.0, self.current_cpu - float(workload.cpu))
        self.current_memory_gb = max(0.0, self.current_memory_gb - float(workload.memory_gb))

    def to_dict(self) -> dict:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["status"] = self.status.value
        data["capabilities"] = sorted(self.capabilities)
        return data

    @classmethod
    def from_dict(cls, data: Mapping) -> "Node":
        payload = dict(data)
        payload["capabilities"] = frozenset(payload.get("capabilities") or ())
        return cls(**payload)


@dataclass
class Workload:
    """A unit of work with explicit resource, cost, energy and locality needs."""

    workload_id: str
    name: str = ""
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    cpu: float = 1.0
    memory_gb: float = 1.0
    gpu: int = 0
    priority: int = 50
    deadline_s: float | None = None
    max_price_per_hour: float | None = None
    energy_budget_wh: float | None = None
    tolerate_fault: bool = True
    require_local: bool = False
    group: str = ""
    state: WorkloadState = WorkloadState.QUEUED
    assigned_node: str | None = None
    submitted_at: float = 0.0
    duration_s: float = 60.0
    retries: int = 0
    idempotency_key: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.workload_id:
            raise ValueError("workload_id required")
        if not isinstance(self.state, WorkloadState):
            self.state = WorkloadState(str(self.state))
        self.required_capabilities = frozenset(str(c) for c in self.required_capabilities)
        self.tags = frozenset(str(t) for t in self.tags)
        _require(self.cpu > 0, "cpu must be > 0")
        _require(self.memory_gb > 0, "memory_gb must be > 0")
        _require(self.gpu >= 0, "gpu must be >= 0")
        _require(0 <= int(self.priority) <= 100, "priority must be in [0, 100]")
        _require(self.duration_s > 0, "duration_s must be > 0")
        _require(self.retries >= 0, "retries must be >= 0")
        self.submitted_at = float(self.submitted_at)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["state"] = self.state.value
        data["required_capabilities"] = sorted(self.required_capabilities)
        data["tags"] = sorted(self.tags)
        return data

    @classmethod
    def from_dict(cls, data: Mapping) -> "Workload":
        payload = dict(data)
        payload["required_capabilities"] = frozenset(payload.get("required_capabilities") or ())
        payload["tags"] = frozenset(payload.get("tags") or ())
        return cls(**payload)


@dataclass
class PlacementScore:
    """The multi-factor score for one (node, workload) pair."""

    node_id: str
    total: float
    components: dict[str, float]
    confidence: float
    feasible: bool = True
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PlacementDecision:
    """A chosen node with alternatives, bottlenecks and an explanation.

    Every important automatic choice in the fleet returns this shape so a
    caller never has to trust a bare node id: the confidence says how close the
    runner-up was, the bottlenecks say what would have to change for a rejected
    node to win, and the explanation carries the raw factor values.
    """

    workload_id: str
    chosen: str | None
    score: float
    confidence: float
    alternatives: list[dict] = field(default_factory=list)
    bottlenecks: list[str] = field(default_factory=list)
    explanation: dict = field(default_factory=dict)

    @property
    def placed(self) -> bool:
        return self.chosen is not None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["placed"] = self.placed
        return data


@dataclass
class FaultForecast:
    """Predicted probability that a node fails inside ``horizon_s``."""

    node_id: str
    horizon_s: float
    risk: float
    drivers: list[str]
    recommendation: str

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# physical models
# --------------------------------------------------------------------------
def capability_match(node: Node, workload: Workload) -> float:
    """Fraction of required capabilities present, with a hard gate at 1.0.

    Returning 0.0 for a partial match would be a lie: a node missing one flag
    is not "close", it cannot run the workload at all. The fraction is only
    used for diagnostics; :func:`place_workload` filters on the hard gate.
    """
    required = workload.required_capabilities
    if not required:
        return 1.0
    return len(required & node.capabilities) / len(required)


def estimate_energy_wh(node: Node, workload: Workload) -> float:
    """Energy for running ``workload`` on ``node``, in watt-hours.

    The common mistake is to multiply peak watts by duration. A machine that is
    already at 80% load only pays the *marginal* draw for new work, so the model
    uses the node's current load to interpolate between idle and peak, then adds
    the workload's own share of the delta.
    """
    hours = max(0.0, float(workload.duration_s)) / 3600.0
    base_load = node.load_fraction
    workload_load = min(1.0, float(workload.cpu) / max(1.0, node.cpu_cores))
    effective_load = _clamp(max(base_load, base_load + workload_load * (1.0 - base_load)))
    watts = node.idle_watts + (node.peak_watts - node.idle_watts) * effective_load
    return round(watts * hours, 6)


def estimate_cost(node: Node, workload: Workload) -> float:
    """Monetary cost of the placement at the node's advertised hourly price."""
    hours = max(0.0, float(workload.duration_s)) / 3600.0
    return round(node.price_per_hour * hours, 6)


def fault_risk(node: Node, horizon_s: float = 3600.0, now: float | None = None) -> FaultForecast:
    """Predict failure probability over ``horizon_s``.

    A reliability number alone is static and forgets wear. The hazard combines:

    * base unreliability (``1 - reliability``),
    * long uptime, because components that have not been power-cycled fail more,
    * heat, because sustained temperature above 70 C is the strongest single
      predictor of an edge device dying,
    * current load, because saturated machines retry and trip,
    * recent faults, because a node that just failed is more likely to fail
      again (bathtub curve's second half).

    Risk is ``1 - exp(-hazard * horizon_hours)`` so it stays in [0, 1) and
    composes across horizons instead of being an arbitrary weighted sum.
    """
    now = time.time() if now is None else float(now)
    horizon_s = max(1.0, float(horizon_s))
    base = max(1e-6, 1.0 - _clamp(node.reliability))
    uptime_days = max(0.0, node.uptime_s) / 86400.0
    uptime_hazard = min(0.65, uptime_days / 120.0)
    heat_hazard = 0.0
    if node.temperature_c > 55.0:
        heat_hazard = min(0.9, (node.temperature_c - 55.0) / 35.0)
    load_hazard = _clamp(node.load_fraction) * 0.35
    fault_hazard = min(1.0, node.fault_count * 0.08)
    staleness_hazard = 0.0
    if node.last_seen:
        age = max(0.0, now - node.last_seen)
        if age > 300:
            staleness_hazard = min(1.0, (age - 300.0) / 3300.0)

    drivers: list[str] = []
    if base >= 0.1:
        drivers.append(f"advertised reliability {node.reliability:.2f}")
    if uptime_hazard >= 0.2:
        drivers.append(f"uptime {uptime_days:.0f}d without power cycle")
    if heat_hazard > 0:
        drivers.append(f"temperature {node.temperature_c:.0f}C")
    if load_hazard >= 0.2:
        drivers.append(f"load {node.load_fraction:.0%}")
    if fault_hazard >= 0.16:
        drivers.append(f"{node.fault_count} recent fault(s)")
    if staleness_hazard > 0:
        drivers.append(f"last seen {max(0.0, now - node.last_seen):.0f}s ago")

    hazard_per_hour = base + uptime_hazard * 0.25 + heat_hazard * 0.35 + load_hazard * 0.2
    hazard_per_hour += fault_hazard * 0.5 + staleness_hazard * 1.2
    risk = 1.0 - math.exp(-hazard_per_hour * (horizon_s / 3600.0))
    risk = round(_clamp(risk, 0.0, 0.999999), 6)

    if risk >= 0.6:
        recommendation = "evacuate"
    elif risk >= 0.3:
        recommendation = "drain-and-inspect"
    elif risk >= 0.12:
        recommendation = "watch"
    else:
        recommendation = "healthy"
    return FaultForecast(node_id=node.node_id, horizon_s=horizon_s, risk=risk,
                         drivers=drivers, recommendation=recommendation)


# --------------------------------------------------------------------------
# placement
# --------------------------------------------------------------------------
#: The weights are deliberately not equal. Capability is a gate; reliability
#: and energy dominate because a cheap placement that dies mid-workload is the
#: most expensive outcome in the fleet.
_WEIGHTS = {
    "capability": 0.0,      # gate, kept for the explanation
    "cpu": 0.16,
    "memory": 0.12,
    "energy": 0.20,
    "cost": 0.12,
    "reliability": 0.22,
    "latency": 0.10,
    "locality": 0.08,
}


def _deadline_margin(node: Node, workload: Workload, transport_latency_ms: float = 0.0) -> float:
    """1.0 when the deadline is comfortably met, 0.0 when it is impossible."""
    if workload.deadline_s is None:
        return 1.0
    transfer_s = transport_latency_ms / 1000.0
    finish_s = workload.duration_s + transfer_s
    if finish_s > workload.deadline_s:
        return 0.0
    return _clamp(1.0 - (finish_s / workload.deadline_s) * 0.5, 0.0, 1.0)


def score_placement(node: Node, workload: Workload, now: float | None = None,
                    transport_latency_ms: float | None = None,
                    federated_credit: float = 1.0) -> PlacementScore:
    """Score one node for one workload.

    A node is feasible only when it has every capability, enough free CPU and
    memory, enough GPUs, and meets any hard price/energy/deadline limits. An
    infeasible node still gets a score with ``feasible=False`` and a human
    reason so the caller can explain rejections instead of silently dropping
    them.
    """
    now = time.time() if now is None else float(now)
    latency = node.latency_ms if transport_latency_ms is None else float(transport_latency_ms)
    reasons: list[str] = []

    if not node.schedulable():
        reasons.append(f"status {node.status.value}")
    if not node.has_capabilities(workload.required_capabilities):
        missing = sorted(set(workload.required_capabilities) - node.capabilities)
        reasons.append("missing capabilities " + ",".join(missing))
    if node.free_cpu < workload.cpu:
        reasons.append(f"cpu {node.free_cpu:.1f}/{workload.cpu:.1f}")
    if node.free_memory_gb < workload.memory_gb:
        reasons.append(f"memory {node.free_memory_gb:.1f}/{workload.memory_gb:.1f}GB")
    if workload.gpu > node.gpu_count:
        reasons.append(f"gpu {node.gpu_count}/{workload.gpu}")
    cost = estimate_cost(node, workload)
    if workload.max_price_per_hour is not None:
        billed = node.price_per_hour
        if billed > workload.max_price_per_hour:
            reasons.append(f"price {billed:.3f}>{workload.max_price_per_hour:.3f}/h")
    energy = estimate_energy_wh(node, workload)
    if workload.energy_budget_wh is not None and energy > workload.energy_budget_wh:
        reasons.append(f"energy {energy:.3f}>{workload.energy_budget_wh:.3f}Wh")
    if workload.require_local and node.region != "local":
        reasons.append(f"region {node.region} is not local")
    margin = _deadline_margin(node, workload, latency)
    if guard := (workload.deadline_s is not None and margin <= 0.0):
        reasons.append("deadline cannot be met")

    feasible = not reasons
    if not feasible:
        return PlacementScore(node_id=node.node_id, total=0.0,
                              components={k: 0.0 for k in _WEIGHTS},
                              confidence=0.0, feasible=False, reason="; ".join(reasons))

    cpu_headroom = _clamp(node.free_cpu / max(1.0, float(node.cpu_cores)))
    mem_headroom = _clamp(node.free_memory_gb / max(0.1, node.memory_gb))
    energy_efficiency = _clamp(1.0 - (energy / max(1e-6, workload.energy_budget_wh
                                               if workload.energy_budget_wh else energy + 25.0)))
    price_ceiling = workload.max_price_per_hour
    if price_ceiling is None:
        cost_score = _clamp(1.0 - min(1.0, cost / 2.0))
    else:
        cost_score = _clamp(1.0 - (cost / max(1e-6, price_ceiling)))
    reliability = _clamp(node.reliability - fault_risk(node, horizon_s=workload.duration_s, now=now).risk)
    latency_score = _clamp(1.0 - latency / 500.0)
    locality = 1.0 if node.region == "local" else _clamp(0.35 * federated_credit)

    components = {
        "capability": capability_match(node, workload),
        "cpu": round(cpu_headroom, 6),
        "memory": round(mem_headroom, 6),
        "energy": round(energy_efficiency, 6),
        "cost": round(cost_score, 6),
        "reliability": round(reliability, 6),
        "latency": round(latency_score, 6),
        "locality": round(locality, 6),
    }
    total = sum(_WEIGHTS[name] * value for name, value in components.items())
    total *= _clamp(0.5 + 0.5 * margin)
    total = round(_clamp(total), 6)
    confidence = round(_clamp(0.45 + 0.55 * total), 6)
    return PlacementScore(node_id=node.node_id, total=total,
                          components=components, confidence=confidence,
                          feasible=True, reason="ok")


def place_workload(nodes: Sequence[Node], workload: Workload,
                   now: float | None = None,
                   remote_latency: Mapping[str, float] | None = None,
                   federated_credit: Mapping[str, float] | None = None,
                   bonuses: Mapping[str, float] | None = None) -> PlacementDecision:
    """Choose the best node for ``workload``.

    ``bonuses`` is how the cross-subsystem judgements enter the choice: the
    energy migration engine names the greenest node, the roaming scheduler names
    its own preference, and each contributes a small additive bonus. The bonus
    is capped below the spread of the weighted factors, so it can break a close
    tie but cannot override capability, headroom or a hard price/energy limit.
    """
    now = time.time() if now is None else float(now)
    remote_latency = dict(remote_latency or {})
    federated_credit = dict(federated_credit or {})
    bonuses = dict(bonuses or {})
    scored: list[PlacementScore] = []
    rejected: list[PlacementScore] = []
    for node in nodes:
        score = score_placement(
            node, workload, now=now,
            transport_latency_ms=remote_latency.get(node.node_id),
            federated_credit=federated_credit.get(node.node_id, 1.0),
        )
        if score.feasible and node.node_id in bonuses:
            bonus = _clamp(float(bonuses[node.node_id]), -0.09, 0.09)
            score.total = round(_clamp(score.total + bonus), 6)
            score.components["cross_system_bonus"] = round(bonus, 6)
        (scored if score.feasible else rejected).append(score)

    scored.sort(key=lambda s: (-s.total, s.node_id))
    bottlenecks = [f"{s.node_id}: {s.reason}" for s in rejected]
    if not scored:
        return PlacementDecision(
            workload_id=workload.workload_id, chosen=None, score=0.0, confidence=0.0,
            alternatives=[], bottlenecks=bottlenecks,
            explanation={"feasible_nodes": 0, "evaluated": len(nodes)},
        )

    best = scored[0]
    runner_up = scored[1].total if len(scored) > 1 else 0.0
    margin = 1.0 if best.total <= 1e-9 else _clamp((best.total - runner_up) / best.total)
    confidence = round(_clamp(0.5 * best.confidence + 0.5 * margin), 6)
    alternatives = [
        {"node_id": s.node_id, "total": s.total,
         "confidence": s.confidence, "components": s.components}
        for s in scored[1:4]
    ]
    if len(scored) == 1:
        bottlenecks.append("only one feasible node; no failover candidate")
    return PlacementDecision(
        workload_id=workload.workload_id,
        chosen=best.node_id,
        score=best.total,
        confidence=confidence,
        alternatives=alternatives,
        bottlenecks=bottlenecks,
        explanation={
            "feasible_nodes": len(scored),
            "evaluated": len(nodes),
            "runner_up": runner_up,
            "margin": round(margin, 6),
            "components": best.components,
            "weights": dict(_WEIGHTS),
        },
    )


# --------------------------------------------------------------------------
# fleet-wide planning
# --------------------------------------------------------------------------
def rebalance_plan(nodes: Sequence[Node], workloads: Sequence[Workload],
                   threshold: float = 0.85) -> dict:
    """Find overloaded nodes and propose moves to colder ones.

    Only workloads whose node is above ``threshold`` are considered, and a move
    is proposed only when the destination is genuinely colder and can host the
    workload. The plan reports the projected load before and after so an
    operator can reject a plan that would create a new hotspot.
    """
    by_id = {n.node_id: n for n in nodes}
    moves: list[dict] = []
    for workload in workloads:
        if workload.state is not WorkloadState.RUNNING or not workload.assigned_node:
            continue
        source = by_id.get(workload.assigned_node)
        if source is None or source.load_fraction < threshold:
            continue
        candidates = [n for n in nodes if n.node_id != source.node_id and n.schedulable()]
        decision = place_workload(candidates, workload)
        if not decision.placed:
            continue
        destination = by_id[decision.chosen]
        if destination.load_fraction >= source.load_fraction - 0.05:
            continue
        moves.append({
            "workload_id": workload.workload_id,
            "from": source.node_id,
            "to": destination.node_id,
            "source_load": round(source.load_fraction, 4),
            "destination_load": round(destination.load_fraction, 4),
            "score": decision.score,
            "confidence": decision.confidence,
        })

    projected: dict[str, float] = {}
    for node in nodes:
        projected[node.node_id] = round(node.load_fraction, 4)
    for move in moves:
        workload = next(w for w in workloads if w.workload_id == move["workload_id"])
        src_load = by_id[move["from"]].load_fraction - workload.cpu / max(1.0, by_id[move["from"]].cpu_cores)
        dst_load = by_id[move["to"]].load_fraction + workload.cpu / max(1.0, by_id[move["to"]].cpu_cores)
        projected[move["from"]] = round(_clamp(src_load), 4)
        projected[move["to"]] = round(_clamp(dst_load), 4)
    return {"moves": moves, "projected_load": projected,
            "threshold": threshold, "count": len(moves)}


def evacuation_plan(nodes: Sequence[Node], workloads: Sequence[Workload],
                    node_id: str) -> dict:
    """Plan the removal of one node without losing its running work.

    A node that cannot be evacuated cleanly is reported as ``stranded`` rather
    than silently dropped: the caller must decide whether to migrate with a
    cold copy, wait for the workload to finish, or accept the loss.
    """
    by_id = {n.node_id: n for n in nodes}
    target = by_id.get(node_id)
    if target is None:
        raise KeyError(f"unknown node {node_id}")
    on_node = [w for w in workloads if w.assigned_node == node_id
               and w.state is WorkloadState.RUNNING]
    others = [n for n in nodes if n.node_id != node_id and n.schedulable()]
    moves: list[dict] = []
    stranded: list[dict] = []
    for workload in on_node:
        decision = place_workload(others, workload)
        if decision.placed:
            moves.append({
                "workload_id": workload.workload_id,
                "from": node_id,
                "to": decision.chosen,
                "score": decision.score,
                "confidence": decision.confidence,
            })
        else:
            stranded.append({
                "workload_id": workload.workload_id,
                "reason": "; ".join(decision.bottlenecks) or "no feasible destination",
            })
    return {"node_id": node_id, "moves": moves, "stranded": stranded,
            "drained": not stranded, "workloads": len(on_node)}


def fleet_health(nodes: Sequence[Node], workloads: Sequence[Workload] | None = None) -> dict:
    """Aggregate health: availability, capacity, utilisation and fault budget."""
    workloads = list(workloads or [])
    total = len(nodes)
    online = [n for n in nodes if n.status is NodeStatus.ONLINE]
    usable = [n for n in nodes if n.schedulable()]
    cpu_capacity = sum(n.cpu_cores for n in usable)
    cpu_used = sum(n.current_cpu for n in usable)
    mem_capacity = sum(n.memory_gb for n in usable)
    mem_used = sum(n.current_memory_gb for n in usable)
    queued = sum(1 for w in workloads if w.state is WorkloadState.QUEUED)
    running = sum(1 for w in workloads if w.state is WorkloadState.RUNNING)
    failed = sum(1 for w in workloads if w.state is WorkloadState.FAILED)
    forecasts = [fault_risk(n) for n in usable]
    at_risk = [f.node_id for f in forecasts if f.risk >= 0.3]
    availability = 1.0 if total == 0 else len(usable) / total
    cpu_util = 0.0 if cpu_capacity == 0 else cpu_used / cpu_capacity
    mem_util = 0.0 if mem_capacity == 0 else mem_used / mem_capacity
    health = round(_clamp(0.5 * availability + 0.3 * (1.0 - max(cpu_util, mem_util))
                          + 0.2 * (1.0 - min(1.0, len(at_risk) / max(1, len(usable))))), 4)
    return {
        "nodes": total, "online": len(online), "usable": len(usable),
        "draining": sum(1 for n in nodes if n.status is NodeStatus.DRAINING),
        "sleeping": sum(1 for n in nodes if n.status is NodeStatus.SLEEPING),
        "availability": round(availability, 4),
        "cpu_capacity": cpu_capacity, "cpu_used": round(cpu_used, 3),
        "cpu_utilisation": round(cpu_util, 4),
        "memory_capacity_gb": round(mem_capacity, 3),
        "memory_used_gb": round(mem_used, 3),
        "memory_utilisation": round(mem_util, 4),
        "queued": queued, "running": running, "failed": failed,
        "at_risk": at_risk, "health": health,
    }


def energy_profile(nodes: Sequence[Node], hours: float = 24.0) -> dict:
    """Projected energy draw if the current load is held for ``hours``."""
    rows = []
    total_wh = 0.0
    for node in nodes:
        if not node.schedulable():
            continue
        load = node.load_fraction
        watts = node.idle_watts + (node.peak_watts - node.idle_watts) * load
        wh = watts * hours
        total_wh += wh
        rows.append({"node_id": node.node_id, "load": round(load, 4),
                     "watts": round(watts, 3), "wh": round(wh, 3),
                     "cost": round(wh / 1000.0 * node.price_per_hour, 4)})
    rows.sort(key=lambda r: -r["wh"])
    return {"hours": hours, "total_wh": round(total_wh, 3),
            "total_kwh": round(total_wh / 1000.0, 4), "nodes": rows}


def predict_fleet_faults(nodes: Sequence[Node], horizon_s: float = 3600.0,
                         now: float | None = None) -> list[FaultForecast]:
    """Forecast every schedulable node, riskiest first."""
    forecasts = [fault_risk(n, horizon_s=horizon_s, now=now)
                 for n in nodes if n.schedulable()]
    forecasts.sort(key=lambda f: (-f.risk, f.node_id))
    return forecasts
