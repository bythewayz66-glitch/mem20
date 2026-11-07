"""Remote experiment lab: run experiments on remote nodes, with estate report."""
from __future__ import annotations
import time, uuid
from . import ecosystem
__all__=["create_experiment","run","compare","experiment_health","experiment_report","probe","estate_context"]

def create_experiment(name, params):
    return {"id": str(uuid.uuid4())[:8], "name": name, "params": params, "status": "created", "results": None}

def run(experiment, runner):
    experiment["status"] = "running"
    res = runner(experiment["params"])
    experiment["results"] = res
    experiment["status"] = "completed"
    experiment["finished"] = time.time()
    return experiment

def compare(experiments):
    return sorted(list(experiments), key=lambda e: -(e.get("results", {}) or {}).get("score", 0))

def experiment_health(experiments):
    done = sum(1 for e in experiments if e.get("status") == "completed")
    return {"total": len(experiments), "completed": done}

def experiment_report():
    e1=create_experiment("a",{"x":1}); e2=create_experiment("b",{"x":2})
    run(e1, lambda p: {"score": p.get("x",0)}); run(e2, lambda p: {"score": p.get("x",0)+1})
    ranked=compare([e1,e2]); h=experiment_health([e1,e2])
    peers={
        "workcell_execution": ecosystem.workcell_execution(e1),
        "node_swarm": ecosystem.node_swarm(),
        "experiment_events": ecosystem.experiment_events("experiment.completed", {"best":ranked[0]["name"],"total":h["total"]}),
        "run_containment": ecosystem.run_containment(e1.get("id","e1")),
        "scenario_compare": ecosystem.scenario_compare(e1.get("results") or {}, e2.get("results") or {}),
        "capability_routing": ecosystem.capability_routing("lab", ["create","run","compare"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"completed":h["completed"],"best":ranked[0]["name"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=experiment_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
