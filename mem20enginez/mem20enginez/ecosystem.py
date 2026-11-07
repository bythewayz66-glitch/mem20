"""Six unique peer adapters for mem20enginez crew runtime (different from #300-#304)."""
from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence


def _safe(name, fn):
    try:
        res = fn() or {}
        return {"ok": True, "subsystem": name, **res}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


# 1) mem20runtimecompatibilityenginez - compatibility checks for members/env
def compat_probe(env: Mapping[str, Any] = None, requirements: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20runtimecompatibilityenginez.domain import check_python, check_deps, compatibility_report, suggest_fixes
        req = dict(requirements or {"python": (3, 11), "deps": ["mem20"]})
        envd = dict(env or {"installed": list(req.get("deps", []))})
        rep = compatibility_report(envd, req)
        fixes = suggest_fixes(rep)
        py = check_python(req.get("python", (3, 11)))
        deps = check_deps(req.get("deps", []), envd.get("installed", []))
        return {"python_ok": py, "deps": deps, "report": rep, "suggest_fixes": fixes}
    return _safe("mem20runtimecompatibilityenginez", run)


# 2) mem20protocolautodiscoveryenginez - protocol discovery/registry for engine wiring
def protocol_discovery(messages: Sequence[str] = None, registry: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20protocolautodiscoveryenginez.domain import detect_protocol, parse_headers, register_protocol, list_protocols, protocol_health
        reg = dict(registry or {"protocols": {}})
        msgs = list(messages or ["GET /health HTTP/1.1\nHost: x\n", '{"type":"ping"}'])
        detected = []
        for m in msgs:
            p = detect_protocol(m)
            detected.append({"sample": str(m)[:40], "protocol": p})
            if p != "unknown":
                reg = register_protocol(reg, p, f"handler:{p}")
        if msgs and "GET" in str(msgs[0]):
            reg = register_protocol(reg, "http", "handler:http")
        headers = parse_headers(str(msgs[0]) if msgs else "")
        return {"detected": detected, "headers": headers, "protocols": list_protocols(reg), "health": protocol_health(reg)}
    return _safe("mem20protocolautodiscoveryenginez", run)


# 3) mem20speculativeworkflowenginez - speculative execution planning
def speculative_plan(workflow: Mapping[str, Any] = None, branches: Sequence[str] = None) -> Dict[str, Any]:
    def run():
        from mem20speculativeworkflowenginez.domain import speculate, commit, rollback, speculative_health
        wf = dict(workflow or {"id": "crew-dispatch", "steps": ["probe", "plan"]})
        br = list(branches or ["probe-fast", "probe-thorough", "plan-greedy"])
        spec = speculate(wf, br)
        spec = commit(spec, br[0] if br else None)
        health = speculative_health(spec)
        return {"workflow": wf, "branches": br, "speculative": spec, "health": health}
    return _safe("mem20speculativeworkflowenginez", run)


# 4) mem20servicebundlingenginez - bundle member capabilities into runtime services
def capability_bundle(services: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20servicebundlingenginez.domain import create_bundle, add_service, discount, bundle_health
        svcs = [dict(s) for s in (services or [{"name": "compat-check", "price": 1}, {"name": "dispatch-plan", "price": 2}, {"name": "member-probe", "price": 1}])]
        bundle = create_bundle(svcs, name="crew-runtime-bundle")
        bundle = discount(bundle, rate=0.1)
        bundle = add_service(bundle, {"name": "telemetry", "price": 0.5})
        health = bundle_health([bundle])
        return {"bundle": bundle, "health": health}
    return _safe("mem20servicebundlingenginez", run)


# 5) mem20predictiverecallenginez - predictive member selection
def predictive_routing(history: Sequence[str] = None, candidates: Sequence[str] = None, context: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20predictiverecallenginez.domain import predict_next, recall_score, prefetch, cache_hit_rate, recall_health
        hist = list(history or ["mem20runtimecompatibilityenginez", "mem20protocolautodiscoveryenginez"])
        cands = list(candidates or ["mem20runtimecompatibilityenginez", "mem20speculativeworkflowenginez", "mem20servicebundlingenginez"])
        preds = predict_next(hist, cands)
        ctx = dict(context or {"recency": {cands[0]: 0.8}, "frequency": {cands[0]: 0.6}})
        scores = {c: recall_score(c, ctx) for c in preds}
        pf = prefetch(preds, k=2)
        rate = cache_hit_rate(3, 4)
        health = recall_health(preds)
        return {"predictions": preds, "scores": scores, "prefetch": pf, "cache_hit_rate": rate, "health": health}
    return _safe("mem20predictiverecallenginez", run)


# 6) mem20customerlifecycleenginez - runtime lifecycle/state transitions
def runtime_lifecycle(customers: Sequence[Mapping[str, Any]] = None) -> Dict[str, Any]:
    def run():
        from mem20customerlifecycleenginez.domain import lifecycle_stage, transition, retention_probability, lifetime_value, segment_customers
        custs = [dict(c) for c in (customers or [{"id": "crew-a", "stage": "new", "mrr": 10}, {"id": "crew-b", "stage": "active", "mrr": 25, "age_months": 6}])]
        stages = {c["id"]: lifecycle_stage(c) for c in custs}
        custs2 = []
        after = {}
        for c in custs:
            c2 = dict(c)
            new_stage = transition(c2, "engage")
            # transition returns stage string; apply it to the customer record
            c2["stage"] = new_stage if isinstance(new_stage, str) else c2.get("stage", "new")
            after[c2["id"]] = c2["stage"]
            custs2.append(c2)
        ret = {c["id"]: retention_probability(c) for c in custs2}
        ltv = {c["id"]: lifetime_value(c) for c in custs2}
        segs = segment_customers(custs2)
        return {"stages": stages, "after_transition": after, "retention": ret, "ltv": ltv, "segments": segs}
    return _safe("mem20customerlifecycleenginez", run)


def probe() -> Dict[str, Any]:
    checks = {
        "runtime_compatibility": compat_probe(),
        "protocol_autodiscovery": protocol_discovery(),
        "speculative_workflow": speculative_plan(),
        "service_bundling": capability_bundle(),
        "predictive_recall": predictive_routing(),
        "customer_lifecycle": runtime_lifecycle(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
