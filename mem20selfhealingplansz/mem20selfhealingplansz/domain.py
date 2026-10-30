"""Self-healing plans: plan execution with auto-repair."""
import time


def create_plan(steps):
    return {"steps": [{"name": s, "status": "pending"} for s in steps], "status": "ready"}


def execute_step(plan, idx, executor):
    step = plan["steps"][idx]
    try:
        executor(step["name"])
        step["status"] = "done"
    except Exception as e:
        step["status"] = "failed"
        step["error"] = str(e)
        # auto-heal: retry once
        try:
            executor(step["name"])
            step["status"] = "healed"
        except Exception as e2:
            step["status"] = "failed"
            step["error"] = str(e2)
    return plan


def plan_status(plan):
    done = sum(1 for s in plan["steps"] if s["status"] in ("done", "healed"))
    failed = sum(1 for s in plan["steps"] if s["status"] == "failed")
    return {"total": len(plan["steps"]), "done": done, "failed": failed, "healed": sum(1 for s in plan["steps"] if s["status"]=="healed")}


def heal_plan(plan):
    for s in plan["steps"]:
        if s["status"] == "failed":
            s["status"] = "pending"
    return plan
