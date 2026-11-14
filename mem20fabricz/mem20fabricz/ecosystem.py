"""Assimilated peers for mem20fabricz: core peers + absorbed member ecosystem aggregation."""
from __future__ import annotations
from typing import Any, Dict, Mapping
import importlib
from . import domain

def _ensure():
    domain._ensure_paths()

def _safe(name, fn):
    try:
        res = fn() or {}
        if isinstance(res, dict) and 'ok' in res:
            return {"subsystem": name, **res}
        return {"ok": True, "subsystem": name, **(res if isinstance(res, dict) else {"result": res})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

# --- Core peers (preserved API) ---
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

def integration_compiler(mapping: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20universalintegrationcompilerz.domain import compile_integration, validate_mapping, transform
        m = dict(mapping or {"source": "a", "target": "b", "fields": {"x": "y"}})
        compiled = compile_integration("source", "target", m.get("fields") or {"x":"y"})
        valid = validate_mapping(m.get("fields") or {"x":"y"}, {"x": "string"}, {"y": "string"})
        out = transform({"x": "hello"}, m.get("fields") or {"x":"y"})
        return {"compiled": compiled, "valid": valid, "transform": out}
    return _safe("mem20universalintegrationcompilerz", run)

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

CORE_CHECKS = {
    "api_gateway": api_gateway,
    "integration_compiler": integration_compiler,
    "episodic_traces": episodic_traces,
    "event_autopilot": event_autopilot,
    "team_radio": team_radio,
    "dispatch_value": dispatch_value,
}

def _probe_member_ecosystem(name: str) -> Dict[str, Any]:
    _ensure()
    try:
        eco = importlib.import_module(f"{name}.ecosystem")
    except Exception as e:
        return {"ok": False, "member": name, "error": f"no_ecosystem:{type(e).__name__}: {e}"}
    try:
        if hasattr(eco, 'probe'):
            r = eco.probe()
            if isinstance(r, dict):
                count = r.get('count')
                if count is None:
                    count = len(r.get('reachable') or r.get('checks') or [])
                return {"ok": bool(r.get('ok', False)), "member": name, "count": int(count)}
            return {"ok": True, "member": name, "count": 1}
        fns = [x for x in dir(eco) if not x.startswith('_') and callable(getattr(eco, x))]
        return {"ok": True, "member": name, "count": len(fns)}
    except Exception as e:
        return {"ok": False, "member": name, "error": f"{type(e).__name__}: {e}"}

def absorbed_member_peers(members=None) -> Dict[str, Any]:
    members = list(members or domain.MEMBERS)
    checks = {}
    total = 0
    ok_members = 0
    for m in members:
        r = _probe_member_ecosystem(m)
        checks[m] = r
        c = r.get('count')
        if isinstance(c, int): total += c
        if r.get('ok'): ok_members += 1
    return {"ok": True, "members_with_ecosystem_probe": len(checks), "members_ok": ok_members, "peer_checks_total": total, "checks": checks}

def probe(include_member_ecosystems: bool = True) -> Dict[str, Any]:
    checks = {k: fn() for k, fn in CORE_CHECKS.items()}
    reachable = [k for k, v in checks.items() if v.get("ok")]
    result = {"ok": len(reachable) == len(CORE_CHECKS), "count": len(reachable), "core_count": len(CORE_CHECKS), "reachable": reachable, "checks": checks}
    if include_member_ecosystems:
        mp = absorbed_member_peers()
        result["member_ecosystems"] = mp
        result["peer_surface_total"] = int(result["core_count"]) + int(mp.get("peer_checks_total", 0))
        result["count"] = result["peer_surface_total"]
    return result
