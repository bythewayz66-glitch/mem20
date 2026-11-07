"""Six unique peers for mem20fabricz Integration Fabric (#311), different from #300-#310."""
from __future__ import annotations
from typing import Any, Dict, Mapping

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# 1) mem20apishapeshiftinggatewayz - payload transform/version routing/schema adaptation
def api_gateway(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20apishapeshiftinggatewayz.domain import transform_payload, version_route, schema_diff, adapt_response
        p = dict(payload or {"id": 1, "name": "demo"})
        mapping = {"name": "title"}
        transformed = transform_payload(p, mapping)
        route = version_route("/v1/items", "v2")
        diff = schema_diff({"name": "string"}, {"title": "string", "id": "int"})
        adapted = adapt_response({"title": "demo"}, "v1")
        return {"transformed": transformed, "route": route, "schema_diff": diff, "adapted": adapted}
    return _safe("mem20apishapeshiftinggatewayz", run)

# 2) mem20universalintegrationcompilerz - compile/validate/transform integration mappings
def integration_compiler(mapping: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20universalintegrationcompilerz.domain import compile_integration, validate_mapping, transform
        m = dict(mapping or {"source": "a", "target": "b", "fields": {"x": "y"}})
        compiled = compile_integration("source", "target", m.get("fields") or {"x":"y"})
        valid = validate_mapping(m.get("fields") or {"x":"y"}, {"x": "string"}, {"y": "string"})
        out = transform({"x": "hello"}, m.get("fields") or {"x":"y"})
        return {"compiled": compiled, "valid": valid, "transform": out}
    return _safe("mem20universalintegrationcompilerz", run)

# 3) mem20episodicmemorygraphz - episode/recall graph for integration traces
def episodic_traces(title: str = "fabric-run") -> Dict[str, Any]:
    def run():
        from mem20episodicmemorygraphz.domain import create_episode, add_event, link_episodes, recall
        ep = create_episode(title, events=[{"type": "dispatch", "member": "m1"}])
        ep = add_event(ep, {"type": "result", "ok": True})
        ep2 = create_episode("fabric-run-2", events=[{"type": "dispatch"}])
        linked = link_episodes([ep, ep2], 0, 1, relation="follows")
        rec = recall([ep, ep2], "dispatch")
        return {"episode": ep, "linked": linked, "recall": rec}
    return _safe("mem20episodicmemorygraphz", run)

# 4) mem20realtimeeventautopilotz - event ingestion/rules/autopilot
def event_autopilot(event: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20realtimeeventautopilotz.domain import ingest_event, evaluate_rules, autopilot
        stream = {"id": "fabric", "events": []}
        ev = dict(event or {"type": "member.failure", "severity": "high"})
        stream = ingest_event(stream, ev)
        rules = [{"match": {"type": "member.failure"}, "action": "reroute"}]
        evald = evaluate_rules(ev, rules)
        auto = autopilot(stream, rules)
        return {"ingested": len(stream.get("events", [])), "rules": evald, "autopilot": auto}
    return _safe("mem20realtimeeventautopilotz", run)

# 5) mem20ambientteamradioz - coordination channel messaging
def team_radio(message: str = "fabric status") -> Dict[str, Any]:
    def run():
        from mem20ambientteamradioz.domain import create_channel, join_channel, send_message, channel_activity
        ch = create_channel("fabric-ops", members=["sys"])
        ch = join_channel(ch, "operator")
        if isinstance(ch, dict): ch.setdefault('messages', [])
        sent = send_message(ch, "sys", message)
        if isinstance(sent, dict) and 'messages' in sent: ch = sent
        elif isinstance(sent, dict) and sent.get('ok') and isinstance(sent.get('message'), dict):
            ch.setdefault('messages', []).append(sent['message'])
        act = channel_activity(ch, window=3600)
        return {"channel": ch.get("name") if isinstance(ch, dict) else "fabric-ops", "activity": act}
    return _safe("mem20ambientteamradioz", run)

# 6) mem20autonomousdealdeskz - priority/value negotiation heuristic for dispatch
def dispatch_value(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20autonomousdealdeskz.domain import price_deal, terms_score, approval_required, deal_health
        p = dict(payload or {"product": {"price": 100}, "customer": {"tier": "gold"}, "value": 12000})
        price = price_deal(p.get("product", {}), p.get("customer", {}), discount_cap=0.2)
        terms = terms_score({"sla": "99.9", "term_months": 12})
        approval = approval_required(float(p.get("value", 0)), threshold=10000)
        health = deal_health({"value": p.get("value", 0), "stage": "dispatch"})
        return {"price": price, "terms_score": terms, "approval_required": approval, "health": health}
    return _safe("mem20autonomousdealdeskz", run)

def probe() -> Dict[str, Any]:
    checks = {
        "api_gateway": api_gateway(), "integration_compiler": integration_compiler(),
        "episodic_traces": episodic_traces(), "event_autopilot": event_autopilot(),
        "team_radio": team_radio(), "dispatch_value": dispatch_value(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
