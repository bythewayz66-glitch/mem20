"""mem20facez service orchestration."""
from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict
from . import domain, ecosystem

class FacezService:
    def status(self) -> Dict[str, Any]:
        st = domain.probe_members(); imp = sum(1 for s in st if s.importable)
        return {"ok": imp == len(st), "members": len(st), "importable": imp, "statuses": [asdict(s) for s in st]}

    def compose(self, intent: str = "workspace", payload: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = payload or {}; plan = domain.compose_plan(intent, payload)
        sig = {
            "multimodal_capture": ecosystem.multimodal_capture(payload),
            "dataflow_compose": ecosystem.dataflow_compose(payload),
            "mission_compile": ecosystem.mission_compile(intent),
            "automation_canvas": ecosystem.automation_canvas(payload),
            "sandbox_world": ecosystem.sandbox_world(payload),
            "agent_blackboard": ecosystem.agent_blackboard(payload),
        }
        return {"ok": True, "plan": asdict(plan), "signals": sig}

    def doctor(self) -> Dict[str, Any]:
        st = domain.probe_members(); sig = ecosystem.probe(); plan = domain.compose_plan("health", {})
        return {"ok": sig.get("ok", False), "members": {"total": len(st), "importable": sum(1 for s in st if s.importable)}, "peers": sig, "sample_plan": asdict(plan)}
