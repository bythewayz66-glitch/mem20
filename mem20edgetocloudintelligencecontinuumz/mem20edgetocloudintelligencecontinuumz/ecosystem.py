"""Cross-subsystem wiring for mem20edgetocloudintelligencecontinuumz (criterion 6).

Six fleet/continuum peers, all different from mem20edgefleetbrainz's set:

1. mem20federatedresearchgridz — federated task distribution across tiers
2. mem20aipipelinecostoptimizerz — cost-aware pipeline/placement economics
3. mem20edgetransportfabricz — transport path, QoS, bandwidth allocation
4. mem20zerodowntimemigrationbrainz — zero-downtime migration verification
5. mem20globalcapabilitymarketplacez — capability discovery/matching
6. mem20resourceexchangemarketz — resource pricing/market signals

Each adapter calls real peer domain APIs and returns structured results.
Failures are reported, never raised into the caller's normal path.
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PROJECTS = (
    "mem20federatedresearchgridz",
    "mem20aipipelinecostoptimizerz",
    "mem20edgetransportfabricz",
    "mem20zerodowntimemigrationbrainz",
    "mem20globalcapabilitymarketplacez",
    "mem20resourceexchangemarketz",
)


def _bootstrap() -> None:
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)


_bootstrap()


def _targets_as_nodes(targets: Sequence[Mapping[str, Any]]) -> list[dict]:
    nodes = []
    for t in targets:
        nodes.append({
            "id": t.get("target_id"),
            "tier": t.get("tier"),
            "capacity": float(t.get("cpu", 1.0)),
            "load": float(t.get("used_cpu", 0.0)),
            "latency": float(t.get("latency_ms", 0.0)),
            "status": t.get("status", "online"),
            "capabilities": list(t.get("capabilities") or []),
        })
    return nodes


def federated_plan(targets: Sequence[Mapping[str, Any]], workload: Mapping[str, Any]) -> dict:
    try:
        from mem20federatedresearchgridz.domain import (
            register_node, distribute_task, grid_health, federated_round,
        )

        grid = {"nodes": [], "tasks": [], "results": []}
        for node in _targets_as_nodes(targets):
            grid = register_node(grid, {
                "id": node["id"], "capacity": node["capacity"], "load": node["load"],
                "status": "active" if node["status"] in ("online", "degraded") else node["status"],
                "tier": node["tier"],
            })
        task = {
            "id": workload.get("workload_id"), "size": float(workload.get("cpu", 1.0)),
            "capability": next(iter(workload.get("required_capabilities") or []), None),
        }
        dist = distribute_task(grid, task)
        round_res = federated_round(grid, task)
        health = grid_health(grid)
        return {
            "ok": True, "subsystem": "mem20federatedresearchgridz",
            "distributed": dist, "round": round_res, "health": health,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20federatedresearchgridz", "error": f"{type(exc).__name__}: {exc}"}


def cost_plan(targets: Sequence[Mapping[str, Any]], workload: Mapping[str, Any]) -> dict:
    try:
        from mem20aipipelinecostoptimizerz.domain import (
            stage_cost, pipeline_cost, bottleneck, optimize_throughput, cost_breakdown,
        )

        stages = []
        throughputs = {}
        for t in targets:
            sid = str(t.get("target_id"))
            # treat target as a stage: cost rate from price, throughput from free cpu/bandwidth
            rate = max(0.0001, float(t.get("cost_per_cpu_hour", 0.0)) + 0.01)
            stages.append({"id": sid, "cost": rate, "parallelism": max(1.0, float(t.get("free_cpu", t.get("cpu", 1.0))))})
            throughputs[sid] = max(0.1, float(t.get("bandwidth_mbps", 10.0)) / 10.0)
        workload_size = max(1.0, float(workload.get("cpu", 1.0)) * float(workload.get("duration_s", 60.0)) / 60.0)
        total = pipeline_cost(stages, workload_size) if stages else 0.0
        bneck = bottleneck(stages, throughputs) if stages else None
        budget = workload.get("max_cost")
        plan = optimize_throughput(stages, float(budget)) if budget is not None and stages else None
        breakdown = cost_breakdown(stages, workload_size) if stages else []
        per_stage = [stage_cost(s, workload_size) for s in stages[:5]]
        return {
            "ok": True, "subsystem": "mem20aipipelinecostoptimizerz",
            "pipeline_cost": total, "bottleneck": bneck, "optimize": plan,
            "breakdown": breakdown, "sample_stage_costs": per_stage,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20aipipelinecostoptimizerz", "error": f"{type(exc).__name__}: {exc}"}


def transport_plan(targets: Sequence[Mapping[str, Any]], source_id: str | None, dest_id: str | None,
                   workload: Mapping[str, Any]) -> dict:
    try:
        from mem20edgetransportfabricz.domain import (
            route_path, qos_class, allocate_bandwidth, transport_health,
        )

        # route_path expects a neighbor map: {node_id: [neighbor_ids...]}
        ids = [str(t.get("target_id")) for t in targets]
        neighbor_map = {nid: [other for other in ids if other != nid] for nid in ids}
        links = [{"id": nid, "status": "up" if next((t for t in targets if str(t.get("target_id")) == nid), {}).get("status") == "online" else "down",
                  "bandwidth_mbps": next((float(t.get("bandwidth_mbps", 0)) for t in targets if str(t.get("target_id")) == nid), 0.0)} for nid in ids]
        src = source_id or (ids[0] if ids else "")
        dst = dest_id or (ids[-1] if ids else src)
        route = route_path(src, dst, neighbor_map) if ids else []
        qos = qos_class(float(workload.get("max_latency_ms") or 200.0), int(workload.get("priority", 50)))
        alloc = allocate_bandwidth(
            sum(float(t.get("bandwidth_mbps", 0)) for t in targets),
            [{"id": workload.get("workload_id", "w"), "demand": float(workload.get("size_mb", 10.0))}],
        )
        health = transport_health(links)
        return {
            "ok": True, "subsystem": "mem20edgetransportfabricz",
            "route": route, "qos": qos, "allocation": alloc, "health": health,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20edgetransportfabricz", "error": f"{type(exc).__name__}: {exc}"}


def migration_semantics(workload: Mapping[str, Any], feasible: bool) -> dict:
    try:
        from mem20zerodowntimemigrationbrainz.domain import (
            ZeroDowntimeMigrationBrain, MigrationNotVerified,
        )

        def verify():
            return {"match": bool(feasible), "old_only": 0 if feasible else 1, "new_only": 0}

        brain = ZeroDowntimeMigrationBrain(verify=verify)
        brain.begin()
        brain.write({"workload_id": workload.get("workload_id")})
        _ = brain.read("state")
        try:
            report = brain.verify_and_cutover()
            return {"ok": True, "subsystem": "mem20zerodowntimemigrationbrainz",
                    "phase": report["phase"], "verified": report["verified"], "rolled_back": brain.rolled_back}
        except MigrationNotVerified as exc:
            brain.rollback()
            return {"ok": True, "subsystem": "mem20zerodowntimemigrationbrainz",
                    "phase": "rollback", "verified": False, "rolled_back": brain.rolled_back,
                    "reason": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20zerodowntimemigrationbrainz", "error": f"{type(exc).__name__}: {exc}"}


def capability_market(targets: Sequence[Mapping[str, Any]], workload: Mapping[str, Any]) -> dict:
    try:
        from mem20globalcapabilitymarketplacez.domain import (
            list_capability, search_marketplace, match, transaction, marketplace_health,
        )

        listings = []
        for t in targets:
            for cap in list(t.get("capabilities") or ["compute"]):
                listings.append(list_capability(t.get("target_id"), cap, float(t.get("cost_per_cpu_hour", 0.0))))
        required = next(iter(workload.get("required_capabilities") or ["compute"]), "compute")
        found = search_marketplace(listings, required)
        matched = match(listings, {"capability": required})
        txn = transaction(matched, "continuum-scheduler") if matched else None
        health = marketplace_health(listings)
        return {
            "ok": True, "subsystem": "mem20globalcapabilitymarketplacez",
            "matches": len(found), "selected": matched, "transaction": txn, "health": health,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20globalcapabilitymarketplacez", "error": f"{type(exc).__name__}: {exc}"}


def resource_market(targets: Sequence[Mapping[str, Any]], workload: Mapping[str, Any]) -> dict:
    try:
        from mem20resourceexchangemarketz.domain import (
            list_resource, buy, price_history, market_health,
        )

        listings = []
        for t in targets:
            listings.append(list_resource(
                t.get("target_id"), "cpu_hour", max(0.0, float(t.get("cpu", 0)) - float(t.get("used_cpu", 0))),
                float(t.get("cost_per_cpu_hour", 0.0)),
            ))
        available = [l for l in listings if l.get("available") and l.get("amount", 0) > 0]
        purchase = buy(dict(available[0]), "continuum-scheduler", min(float(workload.get("cpu", 1.0)), available[0]["amount"])) if available else None
        # price history from synthetic trades
        trades = [{"price": l.get("price", 0), "ts": 0.0} for l in listings]
        history = price_history(trades)
        health = market_health(listings)
        return {
            "ok": True, "subsystem": "mem20resourceexchangemarketz",
            "purchase": purchase, "price_history": history, "health": health,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20resourceexchangemarketz", "error": f"{type(exc).__name__}: {exc}"}


def probe() -> dict:
    report = {
        "mem20federatedresearchgridz": federated_plan([], {"workload_id": "probe", "cpu": 1}),
        "mem20aipipelinecostoptimizerz": cost_plan([], {"workload_id": "probe", "cpu": 1, "duration_s": 60}),
        "mem20edgetransportfabricz": transport_plan([], None, None, {"workload_id": "probe", "max_latency_ms": 100, "priority": 50, "size_mb": 1}),
        "mem20zerodowntimemigrationbrainz": migration_semantics({"workload_id": "probe"}, True),
        "mem20globalcapabilitymarketplacez": capability_market([], {"workload_id": "probe", "required_capabilities": ["compute"]}),
        "mem20resourceexchangemarketz": resource_market([], {"workload_id": "probe", "cpu": 1}),
    }
    reachable = [name for name, val in report.items() if val.get("ok")]
    return {"ok": len(reachable) == len(report), "checks": report, "reachable": reachable, "count": len(reachable)}
