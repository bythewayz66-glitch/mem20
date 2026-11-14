"""Self-healing plans: plan execution with auto-repair, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["create_plan","execute_step","plan_status","heal_plan","healing_report","probe","estate_context"]

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

def healing_report():
    plan=create_plan(["a","b"]); execute_step(plan,0,lambda n: None)
    # simulate one failure+heal
    calls={"n":0}
    def flaky(n):
        calls["n"]+=1
        if calls["n"]==1: raise RuntimeError("x")
    execute_step(plan,1,flaky)
    st=plan_status(plan)
    peers={
        "step_containment": ecosystem.step_containment("b"),
        "healing_events": ecosystem.healing_events("plan.healed", {"healed":st["healed"],"done":st["done"]}),
        "plan_routing": ecosystem.plan_routing("plan", ["execute","heal","retry"]),
        "health_triggers": ecosystem.health_triggers(["executor","plan"]),
        "causal_repair": ecosystem.causal_repair({"failures":st["failed"]},{"failures":1}),
        "recovery_director": ecosystem.recovery_director(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and st["done"]>=1,"done":st["done"],"healed":st["healed"],"failed":st["failed"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=healing_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
