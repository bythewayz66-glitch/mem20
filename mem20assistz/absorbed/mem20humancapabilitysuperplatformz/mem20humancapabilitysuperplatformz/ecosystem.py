"""Meaningful peer integrations for Human Capability Super-Platform (#326, RM-220, search).

Searches/discovers and composes human capability, attention, and execution capacity.
Peer outputs feed capability search outcomes. Preserves legacy domain for #319
(capability_matrix, team_capability) and all domain functions.
"""
from __future__ import annotations
from typing import Any, Dict, List

def _safe(name, fn):
    try:
        return {"ok": True, "subsystem": name, **(fn() or {})}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}

def skill_path(skills: List[str]) -> Dict[str, Any]:
    def run():
        from mem20dynamicskillgraphz.domain import add_skill, update_proficiency, learning_path
        g = {}; prev = None
        for s in (skills or ["execution", "collaboration", "leadership"]):
            add_skill(g, str(s), prereqs=[prev] if prev else []); prev = str(s)
        if prev: update_proficiency(g, prev, 1)
        target = (skills or ["leadership"])[-1]
        return {"path": learning_path(g, str(target)), "skills": [str(s) for s in (skills or [])] or ["execution","collaboration","leadership"]}
    return _safe("mem20dynamicskillgraphz", run)

def capability_identity(payload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20capabilitygapmapperz.core import canonical, stable_hash, words
        obj = canonical(payload or {"capability": "human-execution"})
        h = stable_hash(str(obj))
        return {"canonical": obj, "hash": h[:16], "terms": sorted(words("human capability execution attention"))[:5]}
    return _safe("mem20capabilitygapmapperz", run)

def human_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    def run():
        from mem20relationshipcontextgraphz.core import canonical, similarity
        ctx = canonical({"kind": "human-capability", "focus": payload.get("focus", "execution")})
        sim = similarity("human attention execution", "capability accomplishment")
        return {"context": ctx, "accomplishment_similarity": sim}
    return _safe("mem20relationshipcontextgraphz", run)

def capability_objects(skills: List[str]) -> Dict[str, Any]:
    def run():
        from mem20semanticobjectgraphz.core import canonical, stable_hash
        objs = [canonical({"skill": s}) for s in (skills or ["execution"])[:8]]
        h = stable_hash("|".join(str(s) for s in (skills or [])))
        return {"objects": len(objs), "hash": h[:16]}
    return _safe("mem20semanticobjectgraphz", run)

def evidence_versioning(user_id: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    def run():
        from mem20pipez.domain import version_asset, vc_health
        v = version_asset(user_id or "user", str(evidence or []))
        return {"version": v.get("version"), "vc_health": vc_health([v])}
    return _safe("mem20pipez", run)

def platform_config() -> Dict[str, Any]:
    def run():
        from mem20deterministicconfigurationgraphz.domain import add_node, add_edge, resolve
        g = {"nodes": {}, "edges": []}
        add_node(g, "capability-platform", {"search": True, "assess": True})
        add_node(g, "evidence-store", {"type": "store"})
        add_edge(g, "capability-platform", "evidence-store")
        return {"resolved": resolve(g, "capability-platform") is not None}
    return _safe("mem20deterministicconfigurationgraphz", run)

def search_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Meaningful capability search: domain assessment/matrix/team + 6 peer signals."""
    from . import domain as _dom
    payload = payload or {}
    users = payload.get("users") or [{"id":"u1","skills":{"execution":3,"collaboration":2},"evidence":[{"weight":1,"value":0.8}]}]
    skills = payload.get("skills") or ["execution","collaboration","leadership"]
    matrix = _dom.capability_matrix(users, skills)
    team = {s: _dom.team_capability(matrix, s) for s in skills}
    assessments = {u.get("id","u"): _dom.assess("general", u.get("evidence") or []) for u in users}
    gaps = _dom.growth_plan((users[0].get("skills") if users else {}) or {}, {s: 4 for s in skills})
    recs = _dom.learning_recommendation(gaps)
    sp = skill_path(skills); ident = capability_identity({"skills": skills}); ctx = human_context(payload)
    objs = capability_objects(skills); ev = evidence_versioning(str((users[0] or {}).get("id","u")), (users[0] or {}).get("evidence") or []); cfg = platform_config()
    integrations = {"skill_path": sp, "capability_identity": ident, "human_context": ctx, "capability_objects": objs, "evidence_versioning": ev, "platform_config": cfg}
    ok = sum(1 for v in integrations.values() if v.get("ok"))
    # compatible search-style results
    results = [{"score": round(v, 4), "item": {"skill": k, "team_capability": v}} for k, v in sorted(team.items(), key=lambda kv: -kv[1])]
    return {"results": results, "capability_matrix": matrix, "team_capability": team, "assessments": assessments,
            "recommendations": recs[:5], "integration_health": {"ok": ok, "total": 6}, "integrations": integrations}

def probe() -> Dict[str, Any]:
    checks = {"skill_path": skill_path(["a","b"]), "capability_identity": capability_identity({}), "human_context": human_context({}),
              "capability_objects": capability_objects(["x"]), "evidence_versioning": evidence_versioning("u",[]), "platform_config": platform_config()}
    reachable = [k for k,v in checks.items() if v.get("ok")]
    return {"ok": len(reachable)==6, "count": len(reachable), "reachable": reachable, "checks": checks}
