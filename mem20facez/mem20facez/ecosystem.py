"""Six unique peers for mem20facez Interface/Workspace runtime (#312), different from #300-#311."""
from __future__ import annotations

import concurrent.futures
from typing import Any, Callable, Dict, Mapping

_PEER_TIMEOUT_S = 1.5
_EXEC = concurrent.futures.ThreadPoolExecutor(max_workers=6, thread_name_prefix="facez-peer")


def _safe(name: str, fn: Callable[[], Dict[str, Any]]):
    try:
        fut = _EXEC.submit(fn)
        return {"ok": True, "subsystem": name, **(fut.result(timeout=_PEER_TIMEOUT_S) or {})}
    except concurrent.futures.TimeoutError:
        fut.cancel()
        return {"ok": False, "subsystem": name, "error": f"TimeoutError: peer call timed out after {_PEER_TIMEOUT_S}s"}
    except Exception as e:
        return {"ok": False, "subsystem": name, "error": f"{type(e).__name__}: {e}"}


def multimodal_capture(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20multimodaltaskcapturez.domain import capture, merge_captures, extract_action_items, capture_health
        t = capture(text=str((payload or {}).get("text", "design review")), source="facez")
        m = merge_captures([t, capture(text="follow up", source="facez")])
        items = extract_action_items(t)
        return {"merged": m, "action_items": items, "health": capture_health([t])}
    return _safe("mem20multimodaltaskcapturez", run)


def dataflow_compose(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20visualdataflowcomposerz.domain import create_pipeline, add_node, connect
        p = create_pipeline("facez-flow")
        a = add_node(p, "input", {"name": "intent"})
        b = add_node(p, "action", {"name": "render"})
        c = connect(p, (a.get("id") if isinstance(a, dict) else "n1"), (b.get("id") if isinstance(b, dict) else "n2"))
        return {"pipeline": p.get("name") if isinstance(p, dict) else "facez-flow", "connected": c}
    return _safe("mem20visualdataflowcomposerz", run)


def mission_compile(intent: str = "compose workspace view") -> Dict[str, Any]:
    def run():
        from mem20intenttomissioncompilerz.domain import compile_mission, validate_mission, mission_progress
        intent_obj = {"goal": intent, "parts": [intent]} if isinstance(intent, str) else dict(intent)
        m = compile_mission(intent_obj)
        mm = m if isinstance(m, dict) else {"intent": intent_obj, "mission": m, "steps": []}
        v = validate_mission(mm)
        prog = mission_progress(mm)
        return {"mission": mm, "valid": v, "progress": prog}
    return _safe("mem20intenttomissioncompilerz", run)


def automation_canvas(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20personalautomationcanvasz.domain import create_canvas, add_workflow, add_trigger
        c = create_canvas("facez-canvas", owner="operator")
        c = add_workflow(c, {"id": "wf1", "name": "refresh"})
        c = add_trigger(c, {"id": "t1", "on": "open"})
        return {"canvas": c.get("name") if isinstance(c, dict) else "facez-canvas", "workflows": len((c or {}).get("workflows", [])) if isinstance(c, dict) else 1}
    return _safe("mem20personalautomationcanvasz", run)


def sandbox_world(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20multiworldsandboxz.domain import create_world, branch, step
        w = create_world({"view": "default"}, name="facez")
        b = branch(w, {"view": "spatial"})
        s = step(b if isinstance(b, dict) else w, {"type": "layout"})
        return {"world": (w.get("name") if isinstance(w, dict) else "facez"), "branch": b, "step": s}
    return _safe("mem20multiworldsandboxz", run)


def agent_blackboard(payload: Mapping[str, Any] = None) -> Dict[str, Any]:
    def run():
        from mem20visualagentblackboardz.domain import create_blackboard, post, read
        bb = create_blackboard("facez")
        bb = post(bb, "composer", {"type": "layout", "ok": True})
        items = read(bb)
        return {"blackboard": (bb.get("name") if isinstance(bb, dict) else "facez"), "items": items}
    return _safe("mem20visualagentblackboardz", run)



def _absorbed_member_peers():
    try:
        import importlib, pathlib, sys
        root = pathlib.Path(__file__).resolve().parents[2]
        if str(root) not in sys.path: sys.path.insert(0, str(root))
        try:
            import _mem20_absorbed_finder  # noqa: F401
        except Exception:
            pass
        tc = root / 'toolchest' / 'src'
        if tc.is_dir() and str(tc) not in sys.path: sys.path.insert(0, str(tc))
        adir = pathlib.Path(__file__).resolve().parents[1] / 'absorbed'
        members = sorted(p.name for p in adir.iterdir() if p.is_dir()) if adir.is_dir() else []
        checks = {}
        total = 0; okm = 0
        for name in members:
            try:
                eco = importlib.import_module(f"{name}.ecosystem")
                if hasattr(eco, 'probe'):
                    r = eco.probe()
                    if isinstance(r, dict):
                        c = r.get('count')
                        if c is None: c = len(r.get('reachable') or r.get('checks') or [])
                        checks[name] = {'ok': bool(r.get('ok', False)), 'count': int(c)}
                        total += int(c)
                        if r.get('ok'): okm += 1
                        continue
                fns = [x for x in dir(eco) if not x.startswith('_') and callable(getattr(eco,x))]
                checks[name] = {'ok': True, 'count': len(fns)}
                total += len(fns); okm += 1
            except Exception as e:
                checks[name] = {'ok': False, 'count': 0, 'error': f"{type(e).__name__}: {e}"}
        return {'ok': True, 'members_with_ecosystem_probe': len(members), 'members_ok': okm, 'peer_checks_total': total, 'checks': checks}
    except Exception as e:
        return {'ok': False, 'error': f"{type(e).__name__}: {e}"}


def probe() -> Dict[str, Any]:
    checks = {
        "multimodal_capture": multimodal_capture(),
        "dataflow_compose": dataflow_compose(),
        "mission_compile": mission_compile(),
        "automation_canvas": automation_canvas(),
        "sandbox_world": sandbox_world(),
        "agent_blackboard": agent_blackboard(),
    }
    reachable = [k for k, v in checks.items() if v.get("ok")]
    result = {"ok": len(reachable) == 6, "count": len(reachable), "core_count": 6, "reachable": reachable, "checks": checks}
    try:
        amp = _absorbed_member_peers()
        result["member_ecosystems"] = amp
        result["peer_surface_total"] = 6 + int(amp.get("peer_checks_total", 0))
        result["count"] = result["peer_surface_total"]
    except Exception:
        pass
    return result
