"""Autonomous work cells: task queues, worker assignment, throughput, and estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["create_cell","enqueue","assign_workers","process_next","throughput","cell_health","workcell_report","probe","estate_context"]

def create_cell(name, capacity=4):
    return {"name": name, "capacity": capacity, "queue": [], "workers": [], "completed": 0}

def enqueue(cell, task):
    cell["queue"].append(task)
    return cell

def assign_workers(cell, workers):
    cell["workers"] = workers[: cell["capacity"]]
    return cell

def process_next(cell):
    if not cell["queue"] or not cell["workers"]:
        return None
    task = cell["queue"].pop(0)
    worker = cell["workers"][cell["completed"] % len(cell["workers"])]
    cell["completed"] += 1
    return {"task": task, "worker": worker}

def throughput(cell, window_s=60):
    return round(cell["completed"] / max(1, window_s) * 60, 2)

def cell_health(cell):
    q = len(cell["queue"])
    cap = cell["capacity"]
    return {"queue_depth": q, "utilization": round(min(1.0, q / max(1, cap)), 3), "completed": cell["completed"]}

def workcell_report(cell=None, tasks=None):
    cell = cell or create_cell("cell-a", capacity=4)
    tasks = tasks or [{"id":"t1","capability":"cpu"},{"id":"t2","capability":"io"}]
    for t in tasks: enqueue(cell, t)
    assign_workers(cell, ["w1","w2"])
    processed = process_next(cell)
    health = cell_health(cell); tp = throughput(cell)
    peers = {
        "swarm_workers": ecosystem.swarm_workers(tasks[0] if tasks else {"id":"t1"}, worker_count=len(cell["workers"]) or 2),
        "capability_routing": ecosystem.capability_routing(cell["name"], [t.get("capability","cpu") for t in tasks] or ["cpu"]),
        "work_events": ecosystem.work_events("workcell.report", {"cell":cell["name"],"queue":health["queue_depth"],"completed":cell["completed"]}),
        "cell_containment": ecosystem.cell_containment(cell["name"]),
        "focus_priority": ecosystem.focus_priority({"priority":1,"distractions":max(0,health["queue_depth"]-1),"urgency":0.5}),
        "capacity_forecast": ecosystem.capacity_forecast([max(1,health["queue_depth"])]*5, capacity=cell["capacity"]),
    }
    return {"ok": all(v.get("ok") for v in peers.values()), "cell": cell["name"], "processed": processed is not None, "throughput": tp, "health": health, "peers": peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=workcell_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
