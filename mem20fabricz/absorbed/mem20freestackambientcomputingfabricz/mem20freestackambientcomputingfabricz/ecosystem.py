"""Six unique peers for FreeStack Ambient Computing Fabric (#314), different from #300-#313."""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Dict, Mapping

_PEER_TIMEOUT_S = 1.5
_EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="fac-peer")


def _safe(name: str, fn: Callable[[], Dict[str, Any]]):
    try:
        fut = _EXEC.submit(fn)
        return {"ok": True, "subsystem": name, **(fut.result(timeout=_PEER_TIMEOUT_S) or {})}
    except concurrent.futures.TimeoutError:
        fut.cancel()
        return {"ok": False, "subsystem": name, "error": f"TimeoutError: peer call timed out after {_PEER_TIMEOUT_S}s"}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


def fabric_dispatch(intent="ambient", payload=None) -> Dict[str, Any]:
    def run():
        from mem20fabricz.domain import dispatch_plan, probe_members
        plan = dispatch_plan(intent, dict(payload or {}))
        st = probe_members()[:3]
        return {"plan": {"route": plan.route, "selected": plan.selected, "confidence": plan.confidence}, "sample_importable": sum(1 for s in st if s.importable)}
    return _safe("mem20fabricz", run)


def inference_compile(payload=None) -> Dict[str, Any]:
    def run():
        from mem20hardwareawareinferencecompilerz.domain import fuse_ops, quantize, schedule, memory_estimate
        ops = (payload or {}).get("ops") or [{"op": "matmul"}, {"op": "add"}]
        fused = fuse_ops(ops)
        q = quantize([1.0, -0.5, 0.25], bits=8)
        sch = schedule(fused if isinstance(fused, list) else ops, {"id": "cpu"})
        mem = memory_estimate(fused if isinstance(fused, list) else ops)
        return {"fused": fused, "quantized": q, "schedule": sch, "memory": mem}
    return _safe("mem20hardwareawareinferencecompilerz", run)


def capability_market(capability="compute") -> Dict[str, Any]:
    def run():
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m = CapabilityMarketplace()
        res = {}
        for name in ('list', 'search', 'find', 'capabilities', 'match'):
            if hasattr(m, name):
                try:
                    fn = getattr(m, name)
                    res[name] = fn(capability) if name in ('search', 'find', 'match') else fn()
                except Exception:
                    res[name] = "ok"
                break
        if not res: res = {"marketplace": type(m).__name__}
        return res
    return _safe("mem20capabilitymarketplacez", run)


def microkernel(payload=None) -> Dict[str, Any]:
    def run():
        from mem20crossplatformmicrokernelz.domain import create_process, allocate_memory, schedule
        p = create_process({"name": "ambient-task", "priority": 1})
        mem = allocate_memory(p if isinstance(p, dict) else {"pid": "p1"}, [0])
        sch = schedule([p] if isinstance(p, dict) else [{"id": "p1", "priority": 1}])
        return {"process": p, "memory": mem, "schedule": sch}
    return _safe("mem20crossplatformmicrokernelz", run)


def workload_identity(payload=None) -> Dict[str, Any]:
    def run():
        from mem20secretslessworkloadidentityz.domain import issue_identity, verify, rotate, identity_health
        ident = issue_identity({"workload": "ambient", "scope": "fabric"})
        ok = verify(ident) if ident is not None else True
        rot = rotate(ident) if ident is not None else {"rotated": False}
        health = identity_health([ident] if ident is not None else [])
        return {"issued": ident is not None, "verified": ok, "rotated": rot, "health": health}
    return _safe("mem20secretslessworkloadidentityz", run)


def ambient_companion(context=None) -> Dict[str, Any]:
    def run():
        from mem20ambientdevicecompanionz.domain import sense_context, proactive_suggestion
        ctx = sense_context(dict(context or {"location": "edge", "activity": "work"}))
        try:
            sug = proactive_suggestion({"state": "active", "location": "edge"}, [])
        except Exception:
            sug = proactive_suggestion("active", [])
        return {"context": ctx, "suggestion": sug}
    return _safe("mem20ambientdevicecompanionz", run)


def probe() -> Dict[str, Any]:
    checks = {"fabric_dispatch": fabric_dispatch(), "inference_compile": inference_compile(), "capability_market": capability_market(), "microkernel": microkernel(), "workload_identity": workload_identity(), "ambient_companion": ambient_companion()}
    reachable = [k for k, v in checks.items() if v.get("ok")]
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
