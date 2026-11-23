"""Hot-swappable service foundation: register, swap, health, rollback."""
import time


def register_service(registry, name, impl):
    registry.setdefault("services", {})[name] = {"impl": impl, "version": 1, "status": "active", "swapped_at": time.time()}
    return registry


def swap(registry, name, new_impl):
    svc = registry.get("services", {}).get(name)
    if not svc:
        return {"ok": False, "error": "not found"}
    old = svc["impl"]
    svc["impl"] = new_impl
    svc["version"] += 1
    svc["swapped_at"] = time.time()
    svc["previous"] = old
    return {"ok": True, "version": svc["version"]}


def health(registry):
    svcs = registry.get("services", {})
    return {"total": len(svcs), "active": sum(1 for s in svcs.values() if s["status"] == "active")}


def rollback(registry, name):
    svc = registry.get("services", {}).get(name)
    if not svc or "previous" not in svc:
        return {"ok": False}
    svc["impl"] = svc["previous"]
    del svc["previous"]
    svc["version"] -= 1
    return {"ok": True, "version": svc["version"]}


def list_services(registry):
    return list(registry.get("services", {}).keys())
