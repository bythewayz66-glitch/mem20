"""Real-time event autopilot: event stream, rules, actions, with estate report."""
from __future__ import annotations
import time
from . import ecosystem
__all__=["ingest_event","evaluate_rules","autopilot","throttle","autopilot_health","autopilot_report","probe","estate_context"]

def ingest_event(stream, event):
    stream.setdefault("events", []).append({**event, "ts": time.time()}); return stream

def evaluate_rules(event, rules):
    actions=[]
    for r in rules:
        cond=r.get("condition", lambda e: False)
        if cond(event): actions.append(r.get("action"))
    return actions

def autopilot(stream, rules):
    results=[]
    for e in stream.get("events", []): results.append({"event": e, "actions": evaluate_rules(e, rules)})
    return results

def throttle(stream, max_per_sec=10):
    events=stream.get("events", [])
    if len(events) > max_per_sec: stream["events"]=events[-max_per_sec:]
    return stream

def autopilot_health(stream):
    return {"events": len(stream.get("events", []))}

def autopilot_report():
    stream={}; ingest_event(stream,{"type":"alert","severity":9}); ingest_event(stream,{"type":"info","severity":1})
    rules=[{"condition": lambda e: e.get("severity",0)>5, "action":"notify"}]
    res=autopilot(stream,rules); health=autopilot_health(stream)
    peers={
        "stream_backbone": ecosystem.stream_backbone("autopilot.tick", {"events":health["events"]}),
        "action_containment": ecosystem.action_containment("notify"),
        "healing_actions": ecosystem.healing_actions(["notify","mitigate"]),
        "causal_decisions": ecosystem.causal_decisions({"severity":9},{"severity":1}),
        "health_triggers": ecosystem.health_triggers(["autopilot"]),
        "capability_routing": ecosystem.capability_routing("autopilot", ["ingest","evaluate","act"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"events":health["events"],"actions_triggered":sum(len(r["actions"]) for r in res),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=autopilot_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
