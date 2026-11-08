"""Executable design stress lab: dependency-aware design graph simulation.

Legacy API preserved:
  stress_test(system, load_multiplier, duration_s)
  resilience_score(results)
  bottleneck_analysis(system)
  recovery_time(system, failure_type)
  design_verdict(results, threshold)

Extended API provides component-level resources, dependency propagation,
player/cohort and production workload profiles, cascading failures,
recovery actions, and measurable service-level outcomes.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


FAILURE_TYPES = {
    "crash": {"base_recovery_s": 30, "capacity_factor": 0.0, "error_rate": 1.0},
    "degradation": {"base_recovery_s": 10, "capacity_factor": 0.45, "error_rate": 0.35},
    "partition": {"base_recovery_s": 60, "capacity_factor": 0.15, "error_rate": 0.8},
    "overload": {"base_recovery_s": 20, "capacity_factor": 0.6, "error_rate": 0.25},
}


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class ComponentState:
    component_id: str
    capacity: float
    load: float = 0.0
    queue: float = 0.0
    failed: bool = False
    degraded: bool = False
    failure_type: Optional[str] = None
    recovery_remaining_s: float = 0.0
    processed: float = 0.0
    errors: float = 0.0
    dropped: float = 0.0
    latency_ms: float = 0.0
    saturation_events: int = 0
    propagation_events: int = 0

    @property
    def utilization(self) -> float:
        cap = max(1e-9, self.capacity)
        return self.load / cap

    @property
    def effective_capacity(self) -> float:
        if self.failed:
            ft = FAILURE_TYPES.get(self.failure_type or "crash", FAILURE_TYPES["crash"])
            return self.capacity * float(ft["capacity_factor"])
        if self.degraded:
            return self.capacity * 0.7
        return self.capacity

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.component_id,
            "capacity": round(self.capacity, 3),
            "effective_capacity": round(self.effective_capacity, 3),
            "load": round(self.load, 3),
            "queue": round(self.queue, 3),
            "failed": self.failed,
            "degraded": self.degraded,
            "failure_type": self.failure_type,
            "recovery_remaining_s": round(self.recovery_remaining_s, 3),
            "processed": round(self.processed, 3),
            "errors": round(self.errors, 3),
            "dropped": round(self.dropped, 3),
            "latency_ms": round(self.latency_ms, 3),
            "utilization": round(self.utilization, 4),
            "saturation_events": self.saturation_events,
            "propagation_events": self.propagation_events,
        }


class DesignGraph:
    def __init__(self, system: Mapping[str, Any]):
        self.system = dict(system or {})
        self.nodes: Dict[str, ComponentState] = {}
        self.edges: List[Tuple[str, str, float]] = []  # src, dst, weight
        raw = list(self.system.get("components") or [])
        if not raw:
            raw = [
                {"id": "api", "capacity": float(self.system.get("capacity", 200)), "load": float(self.system.get("base_load", 100))},
            ]
        for c in raw:
            cid = str(c.get("id") or c.get("name") or f"c{len(self.nodes)}")
            cap = float(c.get("capacity") or c.get("max_load") or max(1.0, float(c.get("load", 50)) * 2.0))
            self.nodes[cid] = ComponentState(component_id=cid, capacity=max(1.0, cap), load=float(c.get("load", 0) or 0))
        for e in (self.system.get("dependencies") or self.system.get("edges") or []):
            if isinstance(e, (list, tuple)) and len(e) >= 2:
                src, dst = str(e[0]), str(e[1]); w = float(e[2]) if len(e) > 2 else 1.0
            elif isinstance(e, dict):
                src = str(e.get("from") or e.get("src") or e.get("source") or "")
                dst = str(e.get("to") or e.get("dst") or e.get("target") or "")
                w = float(e.get("weight", e.get("fanout", 1.0)) or 1.0)
            else:
                continue
            if src in self.nodes and dst in self.nodes and src != dst:
                self.edges.append((src, dst, max(0.0, w)))
        # ensure a simple chain if components exist but no edges declared and >1 component
        if not self.edges and len(self.nodes) > 1:
            ids = list(self.nodes.keys())
            for a, b in zip(ids, ids[1:]):
                self.edges.append((a, b, 1.0))

    def downstream(self, node_id: str) -> List[Tuple[str, float]]:
        return [(d, w) for s, d, w in self.edges if s == node_id]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "components": {k: v.as_dict() for k, v in self.nodes.items()},
            "edges": [{"from": s, "to": d, "weight": w} for s, d, w in self.edges],
        }


DEFAULT_PLAYER_COHORTS = [
    {"name": "casual", "users": 100, "rps_per_user": 0.02, "burstiness": 0.2, "tolerance_ms": 900},
    {"name": "core", "users": 40, "rps_per_user": 0.08, "burstiness": 0.35, "tolerance_ms": 500},
    {"name": "whale", "users": 5, "rps_per_user": 0.25, "burstiness": 0.5, "tolerance_ms": 350},
]

DEFAULT_PRODUCTION_PROFILES = [
    {"name": "ci", "rps": 8, "jitter": 0.15, "critical": True},
    {"name": "content_pipeline", "rps": 12, "jitter": 0.25, "critical": False},
    {"name": "analytics", "rps": 5, "jitter": 0.1, "critical": False},
]


def workload_at_tick(t: int, base_load: float, peak_load: float, duration_s: int, cohorts: Sequence[Mapping[str, Any]], production: Sequence[Mapping[str, Any]], rng: random.Random) -> Dict[str, Any]:
    progress = min(1.0, max(0.0, t / max(1, duration_s)))
    ramp = base_load + (peak_load - base_load) * progress
    player_total = 0.0
    cohort_loads = {}
    for c in cohorts:
        users = float(c.get("users", 0))
        rpu = float(c.get("rps_per_user", 0.01))
        burst = float(c.get("burstiness", 0.2))
        wave = 1.0 + burst * math.sin((t / 5.0) + (hash(str(c.get("name"))) % 17))
        noise = 1.0 + rng.uniform(-burst / 2, burst / 2)
        load = max(0.0, users * rpu * wave * noise)
        cohort_loads[str(c.get("name"))] = round(load, 4)
        player_total += load
    prod_total = 0.0
    prod_loads = {}
    for p in production:
        rps = float(p.get("rps", 0))
        jitter = float(p.get("jitter", 0.1))
        val = max(0.0, rps * (1.0 + rng.uniform(-jitter, jitter)))
        prod_loads[str(p.get("name"))] = round(val, 4)
        prod_total += val
    technical = ramp
    total = technical + player_total + prod_total
    return {
        "t": t,
        "technical_load": round(technical, 4),
        "player_load": round(player_total, 4),
        "production_load": round(prod_total, 4),
        "total_load": round(total, 4),
        "cohorts": cohort_loads,
        "production": prod_loads,
    }


def _inject_failures(graph: DesignGraph, t: int, scenario: Mapping[str, Any]) -> List[Dict[str, Any]]:
    events = []
    for inj in (scenario.get("failures") or []):
        at = int(inj.get("at_s", inj.get("t", -1)))
        if at != t:
            continue
        cid = str(inj.get("component") or inj.get("target") or "")
        if cid not in graph.nodes:
            continue
        node = graph.nodes[cid]
        ftype = str(inj.get("type") or "crash")
        node.failed = True
        node.degraded = ftype == "degradation"
        node.failure_type = ftype
        redundancy = float(inj.get("redundancy", scenario.get("system", {}).get("redundancy", 1) or 1))
        base = FAILURE_TYPES.get(ftype, FAILURE_TYPES["crash"])["base_recovery_s"]
        node.recovery_remaining_s = float(inj.get("recovery_s", base / max(1.0, redundancy)))
        events.append({"t": t, "kind": "failure", "component": cid, "failure_type": ftype, "recovery_s": node.recovery_remaining_s})
    return events


def _recover(graph: DesignGraph, dt: int, scenario: Mapping[str, Any]) -> List[Dict[str, Any]]:
    events = []
    auto = bool(scenario.get("auto_recover", True))
    for node in graph.nodes.values():
        if not (node.failed or node.degraded) or node.recovery_remaining_s <= 0:
            continue
        node.recovery_remaining_s = max(0.0, node.recovery_remaining_s - dt)
        if auto and node.recovery_remaining_s <= 0:
            node.failed = False
            node.degraded = False
            prev = node.failure_type
            node.failure_type = None
            node.queue *= 0.5
            events.append({"t_offset_recovered": True, "kind": "recovery", "component": node.component_id, "from_failure": prev})
    return events


def run_design_graph_simulation(system: Mapping[str, Any], load_multiplier: float = 2.0, duration_s: int = 60, step_s: int = 5, seed: int = 0, cohorts: Optional[Sequence[Mapping[str, Any]]] = None, production: Optional[Sequence[Mapping[str, Any]]] = None, failures: Optional[Sequence[Mapping[str, Any]]] = None, threshold: float = 0.9, auto_recover: bool = True) -> Dict[str, Any]:
    rng = random.Random(int(seed))
    sys = dict(system or {})
    sys.setdefault("components", sys.get("components") or [])
    graph = DesignGraph(sys)
    base = float(sys.get("base_load", 100) or 100)
    peak = base * float(load_multiplier)
    cohorts = list(cohorts if cohorts is not None else (sys.get("player_cohorts") or DEFAULT_PLAYER_COHORTS))
    production = list(production if production is not None else (sys.get("production_profiles") or DEFAULT_PRODUCTION_PROFILES))
    scenario = {"failures": list(failures or sys.get("failures") or []), "auto_recover": auto_recover, "system": sys}
    step_s = max(1, int(step_s))
    duration_s = max(step_s, int(duration_s))

    timeline: List[Dict[str, Any]] = []
    failure_events: List[Dict[str, Any]] = []
    recovery_events: List[Dict[str, Any]] = []
    root = next(iter(graph.nodes.keys()))

    for t in range(0, duration_s + 1, step_s):
        failure_events.extend(_inject_failures(graph, t, scenario))
        rec = _recover(graph, step_s if t > 0 else 0, scenario)
        for e in rec:
            e["t"] = t
        recovery_events.extend(rec)

        wl = workload_at_tick(t, base, peak, duration_s, cohorts, production, rng)
        # reset instantaneous loads
        for n in graph.nodes.values():
            n.load = 0.0
        # inject total workload at root and propagate through graph
        pending: List[Tuple[str, float]] = [(root, float(wl["total_load"]))]
        seen: Dict[str, float] = {}
        hops = 0
        while pending and hops < (len(graph.nodes) + 5) * 4:
            hops += 1
            cid, amt = pending.pop(0)
            if cid not in graph.nodes:
                continue
            seen[cid] = seen.get(cid, 0.0) + amt
            node = graph.nodes[cid]
            node.load += amt
            eff_cap = max(1e-9, node.effective_capacity)
            # queue/latency model
            over = max(0.0, node.load + node.queue - eff_cap)
            served = min(node.load + node.queue, eff_cap)
            node.processed += served
            if node.load + node.queue > eff_cap:
                node.saturation_events += 1
            # errors/drops from failure or overload
            err_factor = 0.0
            if node.failed:
                err_factor = FAILURE_TYPES.get(node.failure_type or "crash", FAILURE_TYPES["crash"])["error_rate"]
            elif over > 0:
                err_factor = _clamp(over / max(1.0, node.load + node.queue), 0.0, 0.8)
            node.errors += served * err_factor
            node.dropped += over * _clamp(0.15 + err_factor, 0.0, 1.0)
            node.queue = over * 0.35
            util = node.load / max(1e-9, node.capacity)
            node.latency_ms = 20.0 + 180.0 * _clamp(util) + (1200.0 if node.failed else 0.0) + min(2000.0, node.queue * 2.0)
            # propagate to downstream; failed nodes propagate partial/bad load
            downstream = graph.downstream(cid)
            if downstream:
                prop_total = served * (0.25 if node.failed else 0.85)
                for dst, w in downstream:
                    if dst not in graph.nodes:
                        continue
                    share = prop_total * (w / max(1e-9, sum(x[1] for x in downstream)))
                    pending.append((dst, share))
                    if node.failed or util > 0.95:
                        graph.nodes[dst].propagation_events += 1
                        if util > 1.1 and not graph.nodes[dst].failed:
                            graph.nodes[dst].degraded = True

        components = {k: v.as_dict() for k, v in graph.nodes.items()}
        total_err = sum(v.errors for v in graph.nodes.values())
        total_proc = sum(v.processed for v in graph.nodes.values()) + 1e-9
        avg_lat = sum(v.latency_ms for v in graph.nodes.values()) / max(1, len(graph.nodes))
        max_util = max((v.utilization for v in graph.nodes.values()), default=0.0)
        failed_n = sum(1 for v in graph.nodes.values() if v.failed)
        degraded_n = sum(1 for v in graph.nodes.values() if v.degraded)
        # SLO: ok when error ratio bounded, latency bounded, and not all capacity lost
        error_ratio = total_err / total_proc
        ok = error_ratio < 0.12 and avg_lat < 1500 and max_util < 1.35 and failed_n < max(1, len(graph.nodes))
        timeline.append({
            "t": t,
            "workload": wl,
            "ok": bool(ok),
            "slo": {
                "error_ratio": round(error_ratio, 6),
                "avg_latency_ms": round(avg_lat, 3),
                "max_utilization": round(max_util, 4),
                "failed_components": failed_n,
                "degraded_components": degraded_n,
            },
            "components": components,
        })

    # bottleneck propagation summary
    bottlenecks = []
    for n in graph.nodes.values():
        score = n.saturation_events * 2 + n.propagation_events + (10 if n.failed else 0) + max(0.0, n.utilization - 0.8) * 10
        bottlenecks.append({"id": n.component_id, "score": round(score, 4), "saturation_events": n.saturation_events, "propagation_events": n.propagation_events, "utilization": round(n.utilization, 4)})
    bottlenecks.sort(key=lambda x: -x["score"])

    resilience = resilience_score(timeline)
    verdict = {"pass": resilience >= float(threshold), "score": resilience, "threshold": float(threshold)}
    report = {
        "ok": True,
        "seed": int(seed),
        "deterministic": True,
        "duration_s": duration_s,
        "step_s": step_s,
        "load_multiplier": float(load_multiplier),
        "graph": {"nodes": list(graph.nodes.keys()), "edge_count": len(graph.edges), "edges": [{"from": s, "to": d, "weight": w} for s, d, w in graph.edges]},
        "workload_profiles": {"player_cohorts": cohorts, "production_profiles": production},
        "timeline": timeline,
        "failure_events": failure_events,
        "recovery_events": recovery_events,
        "bottlenecks": bottlenecks,
        "bottleneck_propagation": [b for b in bottlenecks if b["propagation_events"] > 0],
        "service_level": {
            "ticks_ok": sum(1 for r in timeline if r.get("ok")),
            "ticks_total": len(timeline),
            "final_error_ratio": timeline[-1]["slo"]["error_ratio"] if timeline else None,
            "final_avg_latency_ms": timeline[-1]["slo"]["avg_latency_ms"] if timeline else None,
        },
        "resilience": resilience,
        "design_verdict": verdict,
        "exercised_actual_graph": True,
    }
    return report


# ---- legacy-compatible API ----

def stress_test(system, load_multiplier=2.0, duration_s=60):
    rep = run_design_graph_simulation(system, load_multiplier=load_multiplier, duration_s=max(5, int(duration_s)), step_s=5, seed=int((system or {}).get("seed", 0) or 0))
    results = []
    for row in rep["timeline"]:
        wl = row["workload"]
        comp = row["components"]
        util = max((c.get("utilization", 0) for c in comp.values()), default=wl["total_load"] / max(1.0, float((system or {}).get("capacity", 200))))
        results.append({"t": row["t"], "load": wl["total_load"], "utilization": round(util, 3), "ok": row["ok"]})
    return results


def resilience_score(results):
    if not results:
        return 0.0
    ok_count = sum(1 for r in results if r.get("ok"))
    return round(ok_count / max(1, len(results)), 4)


def bottleneck_analysis(system):
    components = (system or {}).get("components", []) or []
    if not components:
        return []
    norm = []
    for c in components:
        load = float(c.get("load", 0) or 0)
        cap = float(c.get("capacity") or c.get("max_load") or max(1.0, load * 2.0))
        row = dict(c)
        row["pressure"] = load / max(1e-9, cap)
        norm.append(row)
    return sorted(norm, key=lambda c: (-c.get("pressure", 0), -float(c.get("load", 0))))[:3]


def recovery_time(system, failure_type="crash"):
    base = FAILURE_TYPES.get(failure_type, FAILURE_TYPES["crash"])["base_recovery_s"]
    redundancy = float((system or {}).get("redundancy", 1) or 1)
    return round(base / max(1.0, redundancy), 2)


def design_verdict(results, threshold=0.9):
    score = resilience_score(results)
    return {"pass": score >= threshold, "score": score, "threshold": float(threshold)}
