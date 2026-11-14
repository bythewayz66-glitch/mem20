"""Energy-aware foundation (RM-036-ish foundation): power monitoring, thresholds, budgets, actions.
Legacy-compatible API preserved: power_reading, threshold_check, energy_budget, optimize_power, daily_energy.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence
import time

# ---- legacy-compatible API ----
def power_reading(device):
    return {"device": device.get("id"), "watts": device.get("power_watts", 0), "timestamp": device.get("ts", 0)}

def threshold_check(reading, threshold_watts):
    if reading["watts"] > threshold_watts:
        return {"exceeded": True, "overage": reading["watts"] - threshold_watts, "device": reading.get("device"), "watts": reading["watts"], "threshold": threshold_watts}
    return {"exceeded": False, "overage": 0, "device": reading.get("device"), "watts": reading["watts"], "threshold": threshold_watts}

def energy_budget(devices, budget_watts):
    total = sum(d.get("power_watts", 0) for d in devices)
    return {"total_watts": total, "budget": budget_watts, "within_budget": total <= budget_watts, "headroom": budget_watts - total}

def optimize_power(devices, target_reduction=0.1):
    actions = []
    for d in devices:
        if d.get("power_watts", 0) > 0:
            actions.append({"device": d.get("id"), "action": "reduce", "target": round(d["power_watts"] * (1 - target_reduction), 2), "current": d["power_watts"]})
    return actions

def daily_energy(devices, hours=24):
    total_kwh = sum(d.get("power_watts", 0) * hours / 1000.0 for d in devices)
    return round(total_kwh, 3)

# ---- advanced domain ----
@dataclass
class Device:
    device_id: str
    power_watts: float = 0.0
    max_watts: float = 0.0
    priority: int = 1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    def to_dict(self): return {"id": self.device_id, "device_id": self.device_id, "power_watts": self.power_watts, "max_watts": self.max_watts, "priority": self.priority, "tags": self.tags}

@dataclass
class Policy:
    policy_id: str
    budget_watts: float
    device_thresholds: Dict[str, float] = field(default_factory=dict)
    default_threshold_watts: float = 0.0
    target_reduction: float = 0.1

def evaluate(devices: Sequence[Mapping[str, Any]], policy: Mapping[str, Any]) -> Dict[str, Any]:
    devs = [dict(d) for d in devices]
    budget = float(policy.get("budget_watts", 0) or 0)
    default_thr = float(policy.get("default_threshold_watts", 0) or 0)
    thresholds = dict(policy.get("device_thresholds") or {})
    readings = [power_reading(d) for d in devs]
    checks = []
    for d, r in zip(devs, readings):
        thr = thresholds.get(d.get("id") or d.get("device_id"), default_thr)
        if thr: checks.append(threshold_check(r, thr))
    b = energy_budget(devs, budget) if budget else {"total_watts": sum(d.get("power_watts",0) for d in devs), "budget": None, "within_budget": True, "headroom": None}
    actions = optimize_power([d for d in devs if not b.get("within_budget", True) or any(c.get("exceeded") and c.get("device")==d.get("id") for c in checks)], float(policy.get("target_reduction", 0.1)))
    return {"readings": readings, "threshold_checks": checks, "budget": b, "actions": actions, "daily_kwh": daily_energy(devs), "ts": time.time(), "ok": b.get("within_budget", True) and not any(c.get("exceeded") for c in checks)}
