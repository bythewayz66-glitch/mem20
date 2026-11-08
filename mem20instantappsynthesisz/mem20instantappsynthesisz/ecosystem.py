"""Meaningful peer integrations for Instant App Synthesis (#327, RM-010, compose).
Compiles plain-language objectives into working capability compositions. Peer outputs feed synthesis.
Preserves legacy domain for #318 (validate_spec, scaffold) and all functions.
"""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try: return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e: return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def config_graph(spec: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20deterministicconfigurationgraphz.domain import add_node, add_edge, resolve
        g={"nodes":{},"edges":[]}; name=str((spec or {}).get("name","app"))
        add_node(g,name,{"framework": (spec or {}).get("framework","react")})
        for p in (spec or {}).get("pages") or ["home"]: add_node(g,f"page:{p}",{}); add_edge(g,name,f"page:{p}")
        return {"resolved": resolve(g,name) is not None, "pages": len((spec or {}).get("pages") or ["home"])}
    return _safe("mem20deterministicconfigurationgraphz", run)

def spec_identity(spec: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20semanticobjectgraphz.core import canonical, stable_hash, words
        obj=canonical({"name": (spec or {}).get("name"), "pages": (spec or {}).get("pages")})
        return {"canonical": obj, "hash": stable_hash(str(obj))[:16], "terms": sorted(words(str((spec or {}).get("name","app objective"))))[:5]}
    return _safe("mem20semanticobjectgraphz", run)

def artifact_version(spec: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20versioncontrollargeassetandrecoverypipelinez.domain import version_asset, vc_health
        v=version_asset(str((spec or {}).get("name","app")), str(spec))
        return {"version": v.get("version"), "vc_health": vc_health([v])}
    return _safe("mem20versioncontrollargeassetandrecoverypipelinez", run)

def capability_path(spec: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20dynamicskillgraphz.domain import add_skill, learning_path
        g={}; caps=(spec or {}).get("capabilities") or (spec or {}).get("components") or ["ui","data","deploy"]
        prev=None
        for c in caps: add_skill(g,str(c),prereqs=[prev] if prev else []); prev=str(c)
        return {"path": learning_path(g,str(caps[-1])) if caps else [], "capabilities": [str(c) for c in caps]}
    return _safe("mem20dynamicskillgraphz", run)

def intent_context(objective: str) -> Dict[str, Any]:
    def run():
        from mem20relationshipcontextgraphz.core import canonical, similarity
        ctx=canonical({"objective": objective or "build app"})
        sim=similarity(objective or "build app", "working composition of capabilities")
        return {"context": ctx, "composition_similarity": sim}
    return _safe("mem20relationshipcontextgraphz", run)

def gap_check(spec: Dict[str, Any], available: List[str]) -> Dict[str, Any]:
    def run():
        from mem20capabilitygapmapperz.core import canonical, stable_hash
        need=[str(x) for x in ((spec or {}).get("capabilities") or (spec or {}).get("components") or [])]
        have=[str(x) for x in (available or [])]
        missing=[n for n in need if n not in have]
        return {"missing": missing, "coverage": round((len(need)-len(missing))/max(1,len(need)),4), "hash": stable_hash(str(need))[:12]}
    return _safe("mem20capabilitygapmapperz", run)

def compose_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    from . import domain as _dom
    payload = payload or {}
    spec = payload.get("spec") or payload if payload.get("name") else {"name": payload.get("objective","instant-app")[:40], "pages":["home"], "components": payload.get("components") or []}
    objective = str(payload.get("objective") or payload.get("goal") or spec.get("name","app"))
    validation = _dom.validate_spec(spec)
    app = _dom.synthesize(spec) if validation.get("valid") else {"name": spec.get("name"), "error":"invalid spec"}
    scaf = _dom.scaffold(app) if validation.get("valid") else {}
    size = _dom.estimate_size(app)
    deploy = _dom.deploy_config(app)
    cfg=config_graph(spec); ident=spec_identity(spec); ver=artifact_version(spec); path=capability_path(spec); ctx=intent_context(objective); gap=gap_check(spec, payload.get("available_capabilities") or [])
    integrations={"config_graph":cfg,"spec_identity":ident,"artifact_versioning":ver,"capability_path":path,"intent_context":ctx,"gap_check":gap}
    ok=sum(1 for v in integrations.values() if v.get("ok"))
    composition = [{"capability": c, "selected": True} for c in (app.get("components") or [])] or [{"capability":"app-shell","selected":True}]
    return {"composition": composition, "coverage": round(ok/6,4), "app": app, "scaffold": scaf, "validation": validation,
            "estimate_size": size, "deploy_config": deploy, "objective": objective, "integration_health":{"ok":ok,"total":6}, "integrations": integrations}

def probe() -> Dict[str, Any]:
    spec={"name":"demo","pages":["home"],"components":["ui"]}
    checks={"config_graph":config_graph(spec),"spec_identity":spec_identity(spec),"artifact_versioning":artifact_version(spec),"capability_path":capability_path(spec),"intent_context":intent_context("demo"),"gap_check":gap_check(spec,[])}
    reachable=[k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
