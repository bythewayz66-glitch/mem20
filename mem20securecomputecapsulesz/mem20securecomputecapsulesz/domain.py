"""Secure compute capsules: sandboxed execution units."""
import uuid, time


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
