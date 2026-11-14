"""Energy-aware compute migration (RM-047): energy/carbon cost and migration.

Legacy-compatible API preserved: `energy_cost`, `migrate_decision`,
`carbon_footprint`, `greenest_node` (tie-break by node id), `migration_plan`.
Extended with a real domain model for battery/thermal/price/renewable-aware
scheduling and migration planning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence
import math
import time


# ---- legacy-compatible API (do not break callers) ----

def energy_cost(node, workload_size):
    power = node.get("power_watts", 100)
    speed = max(0.1, float(node.get("speed", 1.0) or 1.0))
    time_s = float(workload_size) / speed
    kwh = float(power) * time_s / 3600000.0
    rate = float(node.get("energy_rate", 0.12) or 0.12)
    return round(kwh * rate, 6)


def migrate_decision(src, dst, workload):
    src_cost = energy_cost(src, workload.get("size", 1))
    dst_cost = energy_cost(dst, workload.get("size", 1))
    if dst_cost < src_cost * 0.8:
        return {"migrate": True, "savings": round(src_cost - dst_cost, 4), "src_cost": src_cost, "dst_cost": dst_cost}
    return {"migrate": False, "savings": 0.0, "src_cost": src_cost, "dst_cost": dst_cost}


def carbon_footprint(node, workload_size):
    speed = max(0.1, float(node.get("speed", 1.0) or 1.0))
    kwh = float(node.get("power_watts", 100)) * (float(workload_size) / speed) / 3600000.0
    carbon_intensity = float(node.get("carbon_g_per_kwh", 400) or 400)
    return round(kwh * carbon_intensity, 4)


def greenest_node(nodes, workload):
    scored = [(energy_cost(n, workload.get("size", 1)) + carbon_footprint(n, workload.get("size", 1)) * 0.001, n) for n in nodes]
    # Ties are broken by node id, not by comparing the node mappings.
    scored.sort(key=lambda item: (item[0], str(item[1].get("id", ""))))
    return scored[0][1] if scored else None


def migration_plan(workloads, nodes):
    plan = []
    for w in workloads:
        n = greenest_node(nodes, w)
        if n:
            plan.append({"workload": w.get("id"), "target": n.get("id"), "estimated_energy_cost": energy_cost(n, w.get("size", 1)), "estimated_carbon_g": carbon_footprint(n, w.get("size", 1))})
    return plan


# ---- advanced domain ----

@dataclass
class ComputeNode:
    node_id: str
    power_watts: float = 100.0
    speed: float = 1.0
    energy_rate: float = 0.12
    carbon_g_per_kwh: float = 400.0
    battery_pct: Optional[float] = None
    thermal_c: Optional[float] = None
    thermal_limit_c: float = 85.0
    renewable_pct: float = 0.0
    available: bool = True
    region: str = ""
    capacity: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self):
        if not self.node_id: raise ValueError("node_id required")
        if self.speed <= 0: raise ValueError("speed must be > 0")
        if self.power_watts < 0: raise ValueError("power_watts must be >= 0")
        if self.thermal_c is not None and self.thermal_limit_c is not None and self.thermal_c > self.thermal_limit_c + 20:
            pass  # allow representation; feasibility handled separately

    def to_legacy(self) -> Dict[str, Any]:
        return {"id": self.node_id, "node_id": self.node_id, "power_watts": self.power_watts, "speed": self.speed,
                "energy_rate": self.energy_rate, "carbon_g_per_kwh": self.carbon_g_per_kwh,
                "battery_pct": self.battery_pct, "thermal_c": self.thermal_c, "thermal_limit_c": self.thermal_limit_c,
                "renewable_pct": self.renewable_pct, "available": self.available, "region": self.region, "capacity": self.capacity}

    def feasible(self, workload_size: float) -> Dict[str, Any]:
        reasons = []
        if not self.available: reasons.append("node unavailable")
        if self.thermal_c is not None and self.thermal_c >= self.thermal_limit_c: reasons.append("thermal limit reached")
        if self.battery_pct is not None and self.battery_pct < 10 and float(workload_size) > 0: reasons.append("battery critically low")
        return {"ok": len(reasons) == 0, "reasons": reasons}


@dataclass
class Workload:
    workload_id: str
    size: float = 1.0
    priority: int = 1
    deadline_s: Optional[float] = None
    current_node: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_legacy(self): return {"id": self.workload_id, "size": self.size, "priority": self.priority, "current_node": self.current_node}


def score_node(node: ComputeNode, workload: Workload) -> Dict[str, Any]:
    leg = node.to_legacy()
    wl = workload.to_legacy()
    ec = energy_cost(leg, wl["size"])
    cb = carbon_footprint(leg, wl["size"])
    feas = node.feasible(wl["size"])
    renewable_bonus = -ec * (float(node.renewable_pct) / 100.0) * 0.25
    thermal_penalty = 0.0
    if node.thermal_c is not None and node.thermal_limit_c:
        ratio = max(0.0, float(node.thermal_c) / max(1.0, float(node.thermal_limit_c)))
        thermal_penalty = ec * max(0.0, ratio - 0.7) * 0.5
    battery_penalty = 0.0
    if node.battery_pct is not None and node.battery_pct < 30:
        battery_penalty = ec * (1.0 - node.battery_pct / 30.0) * 0.4
    total = ec + cb * 0.001 + renewable_bonus + thermal_penalty + battery_penalty
    if not feas["ok"]: total += 1e9
    return {"node_id": node.node_id, "total_score": round(total, 8), "energy_cost": ec, "carbon_g": cb,
            "feasible": feas["ok"], "reasons": feas["reasons"], "renewable_pct": node.renewable_pct}


def plan_migrations(nodes: Sequence[ComputeNode], workloads: Sequence[Workload], migrate_threshold: float = 0.2) -> Dict[str, Any]:
    node_map = {n.node_id: n for n in nodes}
    placements = []
    migrations = []
    for w in workloads:
        scored = sorted([score_node(n, w) for n in nodes if n.feasible(w.size)["ok"] or True], key=lambda s: (not s["feasible"], s["total_score"], s["node_id"]))
        best = next((s for s in scored if s["feasible"]), scored[0] if scored else None)
        placements.append({"workload_id": w.workload_id, "target": best["node_id"] if best else None, "score": best})
        if best and w.current_node and w.current_node in node_map and w.current_node != best["node_id"]:
            src = node_map[w.current_node]
            dst = node_map[best["node_id"]]
            dec = migrate_decision(src.to_legacy(), dst.to_legacy(), w.to_legacy())
            if dec.get("migrate") or (best["energy_cost"] < energy_cost(src.to_legacy(), w.size) * (1 - migrate_threshold)):
                migrations.append({"workload_id": w.workload_id, "from": w.current_node, "to": best["node_id"], "decision": dec, "target_score": best})
    return {"placements": placements, "migrations": migrations, "counts": {"workloads": len(workloads), "migrations": len(migrations)}}


def fleet_energy_summary(nodes: Sequence[ComputeNode], workloads: Sequence[Workload]) -> Dict[str, Any]:
    total_ec = sum(energy_cost(n.to_legacy(), 1.0) for n in nodes)  # baseline unit
    total_carbon = sum(carbon_footprint(n.to_legacy(), 1.0) for n in nodes)
    plan = plan_migrations(nodes, workloads)
    return {"nodes": len(nodes), "workloads": len(workloads), "baseline_unit_energy_cost": round(total_ec, 6),
            "baseline_unit_carbon_g": round(total_carbon, 4), "planned_migrations": plan["counts"]["migrations"], "plan": plan}
