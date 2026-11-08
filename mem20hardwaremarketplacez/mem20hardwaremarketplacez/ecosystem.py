"""Meaningful peer integrations for Hardware Marketplace (#323, RM-048, match).

Matches workloads to volunteered/owned/rented compute under explicit limits by
composing: fleet placement/energy/cost, device capability/compatibility, data
locality/migration cost, energy/carbon selection, zero-touch swarm availability,
and roaming workload scheduling. Peer outputs feed match scores and outcomes.
"""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def _hw_to_node(hw: Dict[str, Any]):
    hw = hw or {}
    return {"cpu_cores": int(hw.get("cores") or hw.get("cpu_cores") or 4),
            "memory_gb": float(hw.get("memory_gb") or hw.get("memory") or 8.0),
            "gpu_count": int(hw.get("gpu_count") or (1 if hw.get("gpu") else 0)),
            "latency_ms": float(hw.get("latency_ms") or 5.0),
            "price_per_hour": float(hw.get("price") or hw.get("price_per_hour") or 0.0)}

def fleet_fit(listing: Dict[str, Any], workload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20edgefleetbrainz.domain import Node, Workload, estimate_energy_wh, estimate_cost, score_placement
        hw = _hw_to_node(listing.get("hardware_spec") or listing)
        wl_req = workload or {}
        node = Node(node_id=str(listing.get("seller") or listing.get("id") or "node"), **hw)
        wl = Workload(workload_id=str(wl_req.get("id") or "wl"),
                      cpu=float(wl_req.get("cpu") or 1.0), memory_gb=float(wl_req.get("memory_gb") or 1.0),
                      gpu=int(wl_req.get("gpu") or 0), duration_s=float(wl_req.get("duration_s") or 60.0))
        sp = score_placement(node, wl)
        score = float(getattr(sp, "total", sp.get("total", 0.0) if isinstance(sp, dict) else 0.0))
        return {"placement_score": score, "energy_wh": estimate_energy_wh(node, wl), "cost": estimate_cost(node, wl),
                "feasible": bool(getattr(sp, "feasible", True))}
    return _safe("mem20edgefleetbrainz", run)

def capability_fit(listing: Dict[str, Any], workload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20devicecapabilitycompilerz.domain import compile_for_device, compatibility, feature_flags
        hw = listing.get("hardware_spec") or listing
        device_caps = {"gpu": bool(hw.get("gpu") or hw.get("gpu_count")), "memory_gb": float(hw.get("memory_gb") or 8),
                       "cores": int(hw.get("cores") or 4), "cuda": bool(hw.get("cuda") or hw.get("gpu") or hw.get("gpu_count")),
                       "cpu": True}
        needs = list((workload or {}).get("needs") or (["gpu"] if (workload or {}).get("gpu") else ["cpu"]))
        detected = {**device_caps}; comp = compile_for_device({"workload": (workload or {}).get("id","wl"), "needs": needs}, detected)
        compat = compatibility(device_caps, needs)
        flags = feature_flags(device_caps)
        missing = compat.get("missing") or []
        # meaningful: explicit limits - memory/cores must satisfy workload requests
        limits_ok = True
        if (workload or {}).get("memory_gb") and float(device_caps["memory_gb"]) < float(workload["memory_gb"]): limits_ok = False; missing = list(missing)+["memory_gb"]
        if (workload or {}).get("cpu") and int(device_caps["cores"]) < int(workload["cpu"]): limits_ok = False; missing = list(missing)+["cores"]
        compatible = (len(compat.get("missing") or []) == 0) and limits_ok
        return {"compatible": compatible, "missing": missing, "compiled": bool(comp), "feature_flags": flags, "explicit_limits_ok": limits_ok}
    return _safe("mem20devicecapabilitycompilerz", run)

def locality_fit(listing: Dict[str, Any], workload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20datalocalityoptimizerz.domain import optimal_placement, migration_cost, placement_score, locality_report
        hw = listing.get("hardware_spec") or listing
        node = {"id": str(listing.get("seller") or "n"), "latency_ms": float(hw.get("latency_ms") or 10),
                "cost_per_gb": float(hw.get("egress_cost") or 0.05),
                "capacity_gb": float(hw.get("storage_gb") or hw.get("memory_gb") or 100), "used_gb": 0.0,
                "local": bool(listing.get("local", True)), "egress_cost": float(hw.get("egress_cost") or 0.09)}
        data = {"id": str((workload or {}).get("id") or "d"), "size_gb": float((workload or {}).get("data_gb") or 1.0)}
        best = optimal_placement(data, [node, {"id": "remote", "latency_ms": 80, "cost_per_gb": 0.1, "capacity_gb": 9999, "used_gb": 0}])
        mig = migration_cost(data, {"egress_cost": 0.09}, node)
        score = placement_score(node, data)
        rep = locality_report([{"local": bool(best and best.get("id") == node["id"])}])
        return {"placement_score": score, "best_node": (best or {}).get("id"), "migration_cost": mig, "locality": rep}
    return _safe("mem20datalocalityoptimizerz", run)

def energy_fit(listing: Dict[str, Any], workload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20energyawarecomputemigrationz.domain import ComputeNode, Workload as EW, greenest_node, carbon_footprint, energy_cost
        hw = listing.get("hardware_spec") or listing
        nodes_obj = [ComputeNode(str(listing.get("seller") or "n"), power_watts=float(hw.get("power_watts") or 120),
                             renewable_pct=float(hw.get("renewable_pct") or 30), energy_rate=float(hw.get("energy_rate") or 0.12),
                             carbon_g_per_kwh=float(hw.get("carbon_g_per_kwh") or 400), speed=float(hw.get("speed") or 1.0)),
                 ComputeNode("baseline", power_watts=220, renewable_pct=5, carbon_g_per_kwh=600)]
        wl = EW(str((workload or {}).get("id") or "wl"), size=float((workload or {}).get("size") or 1.0))
        leg_nodes = [n.to_legacy() for n in nodes_obj]
        green = greenest_node(leg_nodes, wl.to_legacy())
        leg = green if green else leg_nodes[0]
        return {"greenest": (leg or {}).get("id"), "energy_cost": energy_cost(leg, wl.size),
                "carbon_g": carbon_footprint(leg, wl.size)}
    return _safe("mem20energyawarecomputemigrationz", run)

def swarm_availability(listings: List[Dict[str, Any]], workload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20zerotouchnodeswarmz.domain import register_node, discover, assign_task, load_distribution, heal
        swarm = {"nodes": []}
        for i, l in enumerate(listings or []):
            hw = l.get("hardware_spec") or l
            caps = ["gpu"] if (hw.get("gpu") or hw.get("gpu_count")) else ["cpu"]
            if hw.get("cuda"): caps.append("cuda")
            status = "ready" if l.get("available", True) else "failed"
            swarm = register_node(swarm, {"id": str(l.get("seller") or f"n{i}"), "capabilities": caps, "capacity": 1.0, "load": 0.0, "status": status})
        ready = discover(swarm)
        cap = "gpu" if (workload or {}).get("gpu") else None
        assign = assign_task(swarm, {"id": (workload or {}).get("id","wl"), "capability": cap, "urgency": 0.5})
        healed = heal(swarm)
        dist = load_distribution(healed)
        assigned_to = (assign.get("node") or {}).get("id") if assign.get("node") else None
        return {"ready_nodes": len(ready), "assigned_to": assigned_to, "healed": healed.get("healed", 0), "load_distribution": dist}
    return _safe("mem20zerotouchnodeswarmz", run)

def scheduler_fit(listings: List[Dict[str, Any]], workload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20roamingworkloadschedulerz.domain import schedule, migrate, node_load, scheduler_health
        nodes = []
        for i, l in enumerate(listings or []):
            nodes.append({"id": str(l.get("seller") or f"n{i}"), "load": 0.0, "cpu": int((l.get("hardware_spec") or l).get("cores") or 4)})
        if not nodes: nodes = [{"id":"local","load":0.0,"cpu":4}]
        workloads = [{"id": str((workload or {}).get("id") or "wl"), "cost": float((workload or {}).get("cpu") or 1)}]
        assigns = schedule(workloads, nodes)
        mig = migrate(workloads[0]["id"], "local", assigns[0]["node"]) if assigns else None
        health = scheduler_health(nodes)
        loads = node_load(nodes)
        return {"assignment": assigns[0] if assigns else None, "migration": mig, "health": health, "node_load": loads}
    return _safe("mem20roamingworkloadschedulerz", run)

def match_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Meaningful marketplace match: rank listings for workloads using 6 peer signals."""
    payload = payload or {}
    listings = payload.get("listings") or payload.get("supply") or payload.get("candidates") or []
    workloads = payload.get("workloads") or payload.get("demand") or []
    if not workloads and payload.get("workload"): workloads = [payload["workload"]]
    if not workloads: workloads = [{"id": "wl-default", "cpu": 1, "memory_gb": 1, "data_gb": 1}]
    if not listings:
        listings = [{"seller": "local", "hardware_spec": {"cores": 4, "memory_gb": 8}, "price": 0, "available": True}]
    swarm = swarm_availability(listings, workloads[0])
    sched = scheduler_fit(listings, workloads[0])
    matches = []
    for wl in workloads:
        ranked = []
        for l in listings:
            if not l.get("available", True): continue
            fl = fleet_fit(l, wl); cap = capability_fit(l, wl); loc = locality_fit(l, wl); en = energy_fit(l, wl)
            pscore = float(fl.get("placement_score") or 0.0) if fl.get("ok") else 0.0
            cfit = 1.0 if cap.get("ok") and cap.get("compatible") else 0.0
            lscore = float(loc.get("placement_score") or 0.0) if loc.get("ok") else 0.0
            ecost = float(en.get("energy_cost") or 1.0) if en.get("ok") else 1.0
            score = 0.45*cfit + 0.25*max(0.0, min(1.0, pscore)) + 0.15*max(0.0, min(1.0, lscore*2)) + 0.15*max(0.0, 1.0-min(1.0, ecost*10))
            ranked.append({"listing": {"seller": l.get("seller"), "hardware": l.get("hardware", l.get("hardware_spec")), "price": l.get("price")},
                           "workload": wl.get("id"), "score": round(score, 6), "explicit_limits_ok": cfit == 1.0,
                           "fleet": fl, "capability": cap, "locality": loc, "energy": en})
        ranked.sort(key=lambda x: x["score"], reverse=True)
        if ranked: matches.append({"workload": wl.get("id"), "best": ranked[0], "alternatives": ranked[1:3]})
    integrations = {"edgefleetbrainz": "per-listing fleet_fit", "devicecapabilitycompilerz": "per-listing capability_fit",
                    "datalocalityoptimizerz": "per-listing locality_fit", "energyawarecomputemigrationz": "per-listing energy_fit",
                    "zerotouchnodeswarmz": swarm, "roamingworkloadschedulerz": sched}
    per_listing_ok = 0
    if matches:
        b = matches[0]["best"]
        for k in ["fleet","capability","locality","energy"]:
            if b.get(k,{}).get("ok"): per_listing_ok += 1
    total_ok = per_listing_ok + (1 if swarm.get("ok") else 0) + (1 if sched.get("ok") else 0)
    return {"matches": matches, "unmatched": max(0, len(workloads)-len(matches)), "swarm_availability": swarm,
            "scheduler_fit": sched, "integration_health": {"ok": total_ok, "total": 6}, "integrations": integrations}

def probe() -> Dict[str, Any]:
    dummy_l = [{"seller":"n1","hardware_spec":{"cores":4,"memory_gb":8,"gpu":False},"price":10,"available":True}]
    dummy_w = {"id":"wl","cpu":1,"memory_gb":1}
    checks = {"fleet_fit": fleet_fit(dummy_l[0], dummy_w), "capability_fit": capability_fit(dummy_l[0], dummy_w),
              "locality_fit": locality_fit(dummy_l[0], dummy_w), "energy_fit": energy_fit(dummy_l[0], dummy_w),
              "swarm_availability": swarm_availability(dummy_l, dummy_w), "scheduler_fit": scheduler_fit(dummy_l, dummy_w)}
    reachable = [k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
