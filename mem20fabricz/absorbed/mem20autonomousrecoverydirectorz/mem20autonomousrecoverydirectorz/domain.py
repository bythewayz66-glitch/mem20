"""Autonomous recovery director: incident triage, rollback, remediation, and estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["triage","rollback_plan","remediate","recovery_time","health_after","recovery_report","probe","estate_context"]

def triage(incident):
    sev=incident.get("severity","low"); priority={"critical":1,"high":2,"medium":3,"low":4}.get(sev,4)
    return {"priority":priority,"severity":sev,"auto_remediate":sev in ("low","medium")}

def rollback_plan(state,checkpoint):
    return {"from_version":state.get("version"),"to_version":checkpoint.get("version"),"steps":["stop_writes","restore","verify","resume"]}

def remediate(incident,actions):
    applied=[a for a in actions if a.get("safe",False)]
    return {"applied":applied,"skipped":len(actions)-len(applied)}

def recovery_time(incident):
    return {"critical":5,"high":15,"medium":30,"low":60}.get(incident.get("severity","low"),60)

def health_after(recovery):
    return round(min(1.0,recovery.get("success_rate",0.5)+0.2),3)

def recovery_report(incident=None, state=None, checkpoint=None, actions=None):
    incident=incident or {"severity":"high","component":"api"}; state=state or {"version":2}; checkpoint=checkpoint or {"version":1}; actions=actions or [{"safe":True,"name":"restart"}]
    tr=triage(incident); rb=rollback_plan(state,checkpoint); rem=remediate(incident,actions)
    peers={
        "fault_containment": ecosystem.fault_containment(incident.get("component","api")),
        "healing_plan": ecosystem.healing_plan(["diagnose","isolate","remediate","verify"]),
        "health_signal": ecosystem.health_signal([incident.get("component","api"),"db"]),
        "recovery_pipeline": ecosystem.recovery_pipeline(incident.get("component","api")),
        "incident_events": ecosystem.incident_events(incident),
        "swarm_status": ecosystem.swarm_status("recovery-node"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"triage":tr,"rollback_plan":rb,"remediation":rem,"recovery_time_min":recovery_time(incident),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=recovery_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
