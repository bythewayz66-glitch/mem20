"""Roaming workload scheduler: migrate workloads across nodes, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["schedule","migrate","node_load","scheduler_health","scheduler_report","probe","estate_context"]

def schedule(workloads, nodes):
    assignments=[]
    for w in workloads:
        node=min(nodes, key=lambda n: n.get("load", 0))
        node["load"]=node.get("load", 0) + w.get("cost", 1)
        assignments.append({"workload": w.get("id"), "node": node.get("id")})
    return assignments

def migrate(workload_id, from_node, to_node):
    return {"workload": workload_id, "from": from_node, "to": to_node, "migrated_at": time.time()}

def node_load(nodes):
    return {n.get("id"): n.get("load", 0) for n in nodes}

def scheduler_health(nodes):
    loads=[n.get("load", 0) for n in nodes]
    return {"nodes": len(nodes), "total_load": sum(loads), "max_load": max(loads) if loads else 0}

def scheduler_report():
    nodes=[{"id":"n1","load":0},{"id":"n2","load":0}]
    workloads=[{"id":"w1","cost":2},{"id":"w2","cost":1}]
    assigns=schedule(list(workloads), nodes); mig=migrate("w1","n1","n2"); h=scheduler_health(nodes)
    peers={
        "node_swarm": ecosystem.node_swarm(),
        "workcell_queue": ecosystem.workcell_queue(workloads[0]),
        "capacity_forecast": ecosystem.capacity_forecast([n.get("load",0) for n in nodes]),
        "schedule_events": ecosystem.schedule_events("schedule.report", {"assignments":len(assigns),"total_load":h["total_load"]}),
        "migration_containment": ecosystem.migration_containment("w1"),
        "scheduler_routing": ecosystem.scheduler_routing("scheduler", ["schedule","migrate","balance"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"assignments":len(assigns),"total_load":h["total_load"],"migrated":mig["workload"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=scheduler_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
