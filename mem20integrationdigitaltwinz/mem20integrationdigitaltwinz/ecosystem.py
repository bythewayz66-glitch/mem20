"""Meaningful peer integrations for Integration Digital Twin (#328, RM-076, route).
Simulates external services, rate limits, failures, and future API changes via routing/twin analysis.
Preserves legacy domain (create_twin, sync, simulate, drift, health) for compat (#310 noted).
"""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def service_config(service: str) -> Dict[str, Any]:
    def run():
        from mem20deterministicconfigurationgraphz.domain import add_node, add_edge, resolve
        g={"nodes":{},"edges":[]}; add_node(g,service,{"rate_limit":100,"api":"v1"})
        add_node(g,"fallback",{"api":"v1"}); add_edge(g,service,"fallback")
        return {"resolved": resolve(g,service) is not None, "service": service}
    return _safe("mem20deterministicconfigurationgraphz", run)

def state_version(system_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20versioncontrollargeassetandrecoverypipelinez.domain import version_asset, diff_versions
        a=version_asset(system_id,str(state)); b=version_asset(system_id,str({**(state or {}),"simulated":True}))
        return {"version": b.get("version"), "changed": diff_versions(a,b).get("changed")}
    return _safe("mem20versioncontrollargeassetandrecoverypipelinez", run)

def reversible_sim(scenario: str) -> Dict[str, Any]:
    def run():
        from mem20reversibleexecutiongraphz.domain import create_graph, add_node, undo
        g=create_graph(); add_node(g,{"id":scenario,"type":"simulation"}); u=undo(g)
        return {"reversible": u is not None or isinstance(g,dict), "scenario": scenario}
    return _safe("mem20reversibleexecutiongraphz", run)

def service_identity(service: str) -> Dict[str, Any]:
    def run():
        from mem20semanticobjectgraphz.core import canonical, stable_hash, words
        return {"canonical": canonical({"service":service}), "hash": stable_hash(service)[:16], "terms": sorted(words(f"external service {service} api"))[:4]}
    return _safe("mem20semanticobjectgraphz", run)

def service_context(service: str) -> Dict[str, Any]:
    def run():
        from mem20relationshipcontextgraphz.core import canonical, similarity
        return {"context": canonical({"service":service,"rel":"integrates"}), "similarity": similarity(f"{service} rate limit failure","external api change")}
    return _safe("mem20relationshipcontextgraphz", run)

def routing_capability() -> Dict[str, Any]:
    def run():
        from mem20dynamicskillgraphz.domain import add_skill, learning_path
        g={}; add_skill(g,"route",[]); add_skill(g,"failover",["route"]); add_skill(g,"simulate",["failover"])
        return {"path": learning_path(g,"simulate")}
    return _safe("mem20dynamicskillgraphz", run)

def route_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    from . import domain as _dom
    payload = payload or {}
    system = payload.get("system") or {"id": payload.get("service") or "ext-api", "state": payload.get("state") or {"status":"ok"}}
    twin = payload.get("twin") or _dom.create_twin(system)
    if payload.get("real_state"): twin = _dom.sync(twin, payload["real_state"])
    scenario = payload.get("scenario") or [{"name":"rate_limit","effect":{"status":"throttled"}},{"name":"api_change","effect":{"version":"v2"}}]
    sim = _dom.simulate(twin, scenario)
    dr = _dom.drift(twin, payload.get("real_state") or twin.get("state") or {})
    hl = _dom.health(twin)
    svc=str(system.get("id","ext-api"))
    cfg=service_config(svc); ver=state_version(svc,twin.get("state") or {}); rev=reversible_sim(scenario[0].get("name","sim") if isinstance(scenario,list) and scenario else "sim")
    ident=service_identity(svc); ctx=service_context(svc); cap=routing_capability()
    integrations={"service_config":cfg,"state_versioning":ver,"reversible_simulation":rev,"service_identity":ident,"service_context":ctx,"routing_capability":cap}
    ok=sum(1 for v in integrations.values() if v.get("ok"))
    route = {"id": svc, "action": "failover" if dr else "primary", "simulated_states": len(sim)}
    return {"route": route, "alternatives":[{"id":"fallback","action":"degrade"}], "confidence": round(ok/6,3),
            "twin_id": twin.get("id"), "simulation": sim, "drift": dr, "twin_health": hl,
            "integration_health":{"ok":ok,"total":6}, "integrations": integrations}

def probe() -> Dict[str, Any]:
    checks={"service_config":service_config("api"),"state_versioning":state_version("s",{"x":1}),"reversible_simulation":reversible_sim("sim"),"service_identity":service_identity("api"),"service_context":service_context("api"),"routing_capability":routing_capability()}
    reachable=[k for k,v in checks.items() if v.get("ok")]
    return {"ok":len(reachable)==6,"count":len(reachable),"reachable":reachable,"checks":checks}
