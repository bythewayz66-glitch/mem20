"""Production planning and task orchestration pipeline."""
import time, uuid


def create_plan(tasks, capacity=10):
    # sort by priority desc, schedule within capacity
    tasks = sorted(tasks, key=lambda t: -t.get("priority", 0))
    scheduled = []
    used = 0
    for t in tasks:
        cost = t.get("effort", 1)
        if used + cost <= capacity:
            t["status"] = "scheduled"
            scheduled.append(t)
            used += cost
    return {"scheduled": scheduled, "capacity_used": used, "capacity": capacity}


def orchestrate(tasks, agents):
    assignments = []
    for i, t in enumerate(tasks):
        agent = agents[i % len(agents)] if agents else None
        assignments.append({"task": t.get("id"), "agent": agent})
    return assignments


def bottleneck(tasks):
    # task with highest effort
    if not tasks:
        return None
    return max(tasks, key=lambda t: t.get("effort", 0))


def pipeline_health(tasks):
    done = sum(1 for t in tasks if t.get("status") == "done")
    return {"total": len(tasks), "done": done, "progress": round(done/max(1,len(tasks)),4)}
