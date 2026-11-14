"""Data locality optimizer: placement, migration, cost, with estate report."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["placement_score","optimal_placement","migration_cost","locality_report","rebalance","placement_report","probe","estate_context"]

def placement_score(node, data):
    latency = node.get("latency_ms", 10)
    cost = node.get("cost_per_gb", 0.05)
    capacity = node.get("capacity_gb", 100)
    used = node.get("used_gb", 0)
    free = capacity - used
    if free < data.get("size_gb", 0):
        return -1
    return round(1.0 / (latency + 1) - cost * 0.5, 4)

def optimal_placement(data, nodes):
    scored = [(placement_score(n, data), n) for n in nodes]
    scored = [s for s in scored if s[0] >= 0]
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], str((item[1] or {}).get("id", ""))))
    return scored[0][1]

def migration_cost(data, src, dst):
    size = data.get("size_gb", 0)
    egress = src.get("egress_cost", 0.09)
    return round(size * egress, 4)

def locality_report(placements):
    total = len(placements)
    local = sum(1 for p in placements if p.get("local"))
    return {"total": total, "local": local, "ratio": round(local / max(1, total), 4)}

def rebalance(nodes, data_items):
    assignments = {}
    for d in data_items:
        n = optimal_placement(d, nodes)
        if n:
            assignments[d.get("id")] = n.get("id")
            n["used_gb"] = n.get("used_gb", 0) + d.get("size_gb", 0)
    return assignments

def placement_report(data_items=None, nodes=None):
    data_items = data_items or [{"id":"d1","size_gb":5},{"id":"d2","size_gb":2}]
    nodes = nodes or [{"id":"n1","latency_ms":2,"cost_per_gb":0.02,"capacity_gb":50,"used_gb":0,"local":True},{"id":"n2","latency_ms":15,"cost_per_gb":0.03,"capacity_gb":50,"used_gb":0,"local":False}]
    # work on copies for assignment view
    nodes_copy=[dict(n) for n in nodes]; data_copy=[dict(d) for d in data_items]
    assign=rebalance(nodes_copy,data_copy)
    rep=locality_report([{"local": any(n.get("local") and n.get("id")==nid for n in nodes), "node":nid} for nid in assign.values()])
    mig=migration_cost(data_items[0], nodes[0], nodes[-1]) if len(nodes)>1 else 0
    peers={
        "node_topology": ecosystem.node_topology(nodes),
        "placement_events": ecosystem.placement_events("placement.report", {"assignments":len(assign),"ratio":rep.get("ratio")}),
        "placement_containment": ecosystem.placement_containment(nodes[0].get("id","n1")),
        "node_health": ecosystem.node_health([n.get("id","n") for n in nodes]),
        "placement_routing": ecosystem.placement_routing("place-1", ["latency","cost","capacity"]),
        "capacity_forecast": ecosystem.capacity_forecast([n.get("used_gb",0)+5 for n in nodes]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"assignments":assign,"locality":rep,"migration_cost_sample":mig,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=placement_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
