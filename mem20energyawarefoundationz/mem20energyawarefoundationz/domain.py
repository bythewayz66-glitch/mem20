"""Energy-aware foundation: power monitoring, thresholds, actions."""
import math


def power_reading(device):
    return {"device": device.get("id"), "watts": device.get("power_watts", 0), "timestamp": device.get("ts", 0)}


def threshold_check(reading, threshold_watts):
    if reading["watts"] > threshold_watts:
        return {"exceeded": True, "overage": reading["watts"] - threshold_watts}
    return {"exceeded": False, "overage": 0}


def energy_budget(devices, budget_watts):
    total = sum(d.get("power_watts", 0) for d in devices)
    return {"total_watts": total, "budget": budget_watts, "within_budget": total <= budget_watts, "headroom": budget_watts - total}


def optimize_power(devices, target_reduction=0.1):
    actions = []
    for d in devices:
        if d.get("power_watts", 0) > 0:
            actions.append({"device": d.get("id"), "action": "reduce", "target": round(d["power_watts"] * (1 - target_reduction), 2)})
    return actions


def daily_energy(devices, hours=24):
    total_kwh = sum(d.get("power_watts", 0) * hours / 1000.0 for d in devices)
    return round(total_kwh, 3)
