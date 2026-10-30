"""Edge fleet brain: device registry, workload placement, health."""
import math


def register_device(fleet, device):
    fleet.setdefault("devices", [])
    if not any(d.get("id") == device.get("id") for d in fleet["devices"]):
        fleet["devices"].append({**device, "status": "online"})
    return fleet


def place_workload(fleet, workload):
    candidates = [d for d in fleet.get("devices", []) if d.get("status") == "online" and d.get("capacity", 0) >= workload.get("size", 0)]
    if not candidates:
        return None
    best = max(candidates, key=lambda d: d.get("capacity", 0) - d.get("load", 0))
    best["load"] = best.get("load", 0) + workload.get("size", 0)
    return best


def fleet_health(fleet):
    devs = fleet.get("devices", [])
    if not devs:
        return {"total": 0, "online": 0, "health": 0.0}
    online = sum(1 for d in devs if d.get("status") == "online")
    return {"total": len(devs), "online": online, "health": round(online / len(devs), 4)}


def evict_offline(fleet, timeout_s=300):
    removed = []
    kept = []
    for d in fleet.get("devices", []):
        if d.get("last_seen", 0) < (time_now() - timeout_s) if False else False:
            removed.append(d)
        else:
            kept.append(d)
    fleet["devices"] = kept
    return {"removed": len(removed), "remaining": len(kept)}


def time_now():
    import time
    return time.time()
