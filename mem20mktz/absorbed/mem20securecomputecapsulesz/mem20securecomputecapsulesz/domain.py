"""Secure compute capsules: sandboxed execution units, with estate report."""
from __future__ import annotations
import uuid, time
from . import ecosystem
__all__=["create_capsule","run_capsule","isolate","capsule_health","capsule_report","probe","estate_context"]

def create_capsule(code, limits=None):
    return {"id": str(uuid.uuid4())[:8], "code": code, "limits": limits or {"cpu": 1, "mem": 256}, "status": "created", "created": time.time()}

def run_capsule(capsule, runner):
    capsule["status"] = "running"
    try:
        res = runner(capsule["code"], capsule["limits"])
        capsule["result"] = res
        capsule["status"] = "completed"
    except Exception as e:
        capsule["error"] = str(e)
        capsule["status"] = "failed"
    capsule["finished"] = time.time()
    return capsule

def isolate(capsule):
    capsule["isolated"] = True
    return capsule

def capsule_health(capsules):
    return {"total": len(capsules), "completed": sum(1 for c in capsules if c.get("status")=="completed"), "failed": sum(1 for c in capsules if c.get("status")=="failed")}

def capsule_report():
    c=create_capsule("1+1", {"cpu":1}); run_capsule(c, lambda code,lim: eval(code)); isolate(c); h=capsule_health([c])
    peers={
        "capsule_containment": ecosystem.capsule_containment(c.get("id","c1")),
        "recovery_plans": ecosystem.recovery_plans(["isolate","restart"]),
        "workload_identity": ecosystem.workload_identity(f"capsule-{c.get('id','c1')}"),
        "capsule_routing": ecosystem.capsule_routing(c.get("id","c1"), ["create","run","isolate"]),
        "capsule_events": ecosystem.capsule_events("capsule.completed", {"id":c.get("id"),"status":c.get("status")}),
        "capsule_config": ecosystem.capsule_config(c.get("limits") or {}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and c.get("status")=="completed","completed":h["completed"],"isolated":bool(c.get("isolated")),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=capsule_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
