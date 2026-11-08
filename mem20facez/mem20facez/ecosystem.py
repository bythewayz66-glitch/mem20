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
    return {"ok": len(reachable) == 6, "count": len(reachable), "reachable": reachable, "checks": checks}
