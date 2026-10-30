"""Autonomous recovery director: incident triage, rollback, remediation."""
import time


def triage(incident):
    sev = incident.get("severity", "low")
    priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(sev, 4)
    return {"priority": priority, "severity": sev, "auto_remediate": sev in ("low", "medium")}


def rollback_plan(state, checkpoint):
    return {"from_version": state.get("version"), "to_version": checkpoint.get("version"), "steps": ["stop_writes", "restore", "verify", "resume"]}


def remediate(incident, actions):
    applied = []
    for a in actions:
        if a.get("safe", False):
            applied.append(a)
    return {"applied": applied, "skipped": len(actions) - len(applied)}


def recovery_time(incident):
    base = {"critical": 5, "high": 15, "medium": 30, "low": 60}.get(incident.get("severity", "low"), 60)
    return base


def health_after(recovery):
    return round(min(1.0, recovery.get("success_rate", 0.5) + 0.2), 3)
