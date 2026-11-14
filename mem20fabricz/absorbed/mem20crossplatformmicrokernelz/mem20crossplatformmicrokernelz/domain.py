"""Cross-platform microkernel: process, memory, IPC, scheduling, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_process","allocate_memory","ipc_send","schedule","context_switch","kill","microkernel_report","probe","estate_context"]

def create_process(pid, priority=0):
    return {"pid": pid, "priority": priority, "state": "ready", "memory_pages": [], "created_at": time.time()}
def allocate_memory(proc, pages):
    proc["memory_pages"].extend(pages); return proc
def ipc_send(sender, receiver, message):
    return {"from": sender, "to": receiver, "message": message, "ts": time.time(), "delivered": True}
def schedule(processes):
    ready = [p for p in processes if p.get("state") == "ready"]; ready.sort(key=lambda p: -p.get("priority", 0)); return ready
def context_switch(current, nxt):
    return {"from": current.get("pid") if current else None, "to": nxt.get("pid"), "saved": True}
def kill(proc):
    proc["state"] = "terminated"; proc["memory_pages"] = []; return proc

def microkernel_report(procs=None):
    procs = procs or [create_process("p1",1), create_process("p2",0)]
    allocate_memory(procs[0],[1,2]); sched=schedule(procs); cs=context_switch(None,sched[0]) if sched else None; msg=ipc_send("p1","p2","ping")
    peers={
        "node_swarm": ecosystem.node_swarm(procs[0]),
        "ipc_events": ecosystem.ipc_events("ipc.send", {"from":msg["from"],"to":msg["to"]}),
        "process_containment": ecosystem.process_containment(procs[0]["pid"]),
        "kernel_health": ecosystem.kernel_health(["scheduler","ipc","memory"]),
        "capability_routing": ecosystem.capability_routing("ipc", ["ipc","sched","mem"]),
        "memory_locality": ecosystem.memory_locality(procs[0]["memory_pages"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"scheduled":len(sched),"ipc_delivered":msg["delivered"],"context_switch":cs is not None,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=microkernel_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
