"""Production planning and task orchestration pipeline, with estate report."""
from __future__ import annotations
import time, uuid
from . import ecosystem
__all__=["create_plan","orchestrate","bottleneck","pipeline_health","orchestration_report","probe","estate_context"]

def create_plan(tasks, capacity=10):
    tasks = sorted(list(tasks), key=lambda t: -t.get("priority", 0))
    scheduled=[]; used=0
    for t in tasks:
        t=dict(t); cost=t.get("effort",1)
        if used + cost <= capacity:
            t["status"]="scheduled"; scheduled.append(t); used+=cost
    return {"scheduled": scheduled, "capacity_used": used, "capacity": capacity}

def orchestrate(tasks, agents):
    assignments=[]
    for i,t in enumerate(tasks):
        agent=agents[i % len(agents)] if agents else None
        assignments.append({"task": t.get("id"), "agent": agent})
    return assignments

def bottleneck(tasks):
    if not tasks: return None
    return max(tasks, key=lambda t: t.get("effort", 0))

def pipeline_health(tasks):
    done = sum(1 for t in tasks if t.get("status") == "done")
    return {"total": len(tasks), "done": done, "progress": round(done/max(1,len(tasks)),4)}

def orchestration_report(tasks=None, agents=None):
    tasks = tasks or [{"id":"t1","priority":2,"effort":2},{"id":"t2","priority":1,"effort":3,"status":"done"}]
    agents = agents or ["a1","a2"]
    plan=create_plan(tasks, capacity=10); assigns=orchestrate(plan["scheduled"], agents); bn=bottleneck(tasks); health=pipeline_health(tasks)
    peers={
        "workcells": ecosystem.workcells(tasks[0] if tasks else {"id":"t1"}),
        "node_swarm": ecosystem.node_swarm(),
        "capacity_plan": ecosystem.capacity_plan([t.get("effort",1) for t in tasks]),
        "task_containment": ecosystem.task_containment(tasks[0].get("id","t1") if tasks else "t1"),
        "orchestration_events": ecosystem.orchestration_events("orchestration.report", {"scheduled":len(plan["scheduled"]),"assignments":len(assigns)}),
        "capability_routing": ecosystem.capability_routing("plan", ["schedule","orchestrate","execute"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"scheduled":len(plan["scheduled"]),"assignments":len(assigns),"bottleneck":(bn.get("id") if isinstance(bn,dict) else None),"health":health,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=orchestration_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
