"""Live project demonstration engine: demo flows, steps, narration."""
import time


def create_demo(project, steps=None):
    return {"project": project, "steps": list(steps or []), "current": 0, "status": "ready", "started_at": None}


def add_step(demo, step):
    demo["steps"].append(step)
    return demo


def start(demo):
    demo["status"] = "running"
    demo["started_at"] = time.time()
    demo["current"] = 0
    return demo


def advance(demo):
    if demo["current"] < len(demo["steps"]) - 1:
        demo["current"] += 1
        return {"ok": True, "current": demo["current"]}
    demo["status"] = "finished"
    return {"ok": False, "reason": "end"}


def progress(demo):
    total = len(demo["steps"])
    return {"current": demo["current"], "total": total, "progress": round(demo["current"]/max(1,total),4)}
