"""Universal health nervous system: aggregate health across subsystems."""
import time


def register_subsystem(health, name, checker):
    health.setdefault("subsystems", {})[name] = {"checker": checker, "last": None, "status": "unknown"}
    return health


def check_all(health):
    results = {}
    for name, info in health.get("subsystems", {}).items():
        try:
            r = info["checker"]()
            info["last"] = r
            info["status"] = "healthy" if r.get("ok", True) else "unhealthy"
        except Exception as e:
            info["last"] = {"error": str(e)}
            info["status"] = "error"
        results[name] = info["status"]
    return results


def overall(health):
    statuses = [s["status"] for s in health.get("subsystems", {}).values()]
    if any(s == "error" for s in statuses):
        return "degraded"
    if all(s == "healthy" for s in statuses):
        return "healthy"
    if any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    return "unknown"


def health_report(health):
    return {"overall": overall(health), "subsystems": {n: i["status"] for n, i in health.get("subsystems", {}).items()}}
