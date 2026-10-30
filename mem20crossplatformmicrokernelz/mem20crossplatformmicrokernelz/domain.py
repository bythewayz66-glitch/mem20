"""Cross-platform microkernel: process, memory, IPC, scheduling."""
import time


def create_process(pid, priority=0):
    return {"pid": pid, "priority": priority, "state": "ready", "memory_pages": [], "created_at": time.time()}


def allocate_memory(proc, pages):
    proc["memory_pages"].extend(pages)
    return proc


def ipc_send(sender, receiver, message):
    return {"from": sender, "to": receiver, "message": message, "ts": time.time(), "delivered": True}


def schedule(processes):
    ready = [p for p in processes if p.get("state") == "ready"]
    ready.sort(key=lambda p: -p.get("priority", 0))
    return ready


def context_switch(current, nxt):
    return {"from": current.get("pid") if current else None, "to": nxt.get("pid"), "saved": True}


def kill(proc):
    proc["state"] = "terminated"
    proc["memory_pages"] = []
    return proc
