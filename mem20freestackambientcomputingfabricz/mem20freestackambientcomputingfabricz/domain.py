"""Free-stack ambient computing fabric: resource pooling, discovery, allocation."""
import math


def pool_resources(nodes):
    total_cpu = sum(n.get("cpu", 0) for n in nodes)
    total_mem = sum(n.get("memory", 0) for n in nodes)
    total_storage = sum(n.get("storage", 0) for n in nodes)
    return {"cpu": total_cpu, "memory": total_mem, "storage": total_storage, "nodes": len(nodes)}


def discover_services(fabric, capability):
    return [s for s in fabric.get("services", []) if capability in s.get("capabilities", [])]


def allocate(fabric, request):
    pool = fabric.get("pool", {})
    if pool.get("cpu", 0) >= request.get("cpu", 0) and pool.get("memory", 0) >= request.get("memory", 0):
        pool["cpu"] -= request.get("cpu", 0)
        pool["memory"] -= request.get("memory", 0)
        return {"allocated": True, "remaining": dict(pool)}
    return {"allocated": False, "remaining": dict(pool)}


def fabric_health(fabric):
    nodes = fabric.get("nodes", [])
    if not nodes:
        return {"health": 0.0}
    online = sum(1 for n in nodes if n.get("status") == "online")
    return {"total": len(nodes), "online": online, "health": round(online / len(nodes), 4)}


def ambient_score(fabric):
    return round(fabric.get("pool", {}).get("cpu", 0) / max(1, fabric.get("total_cpu", 1)), 4)
