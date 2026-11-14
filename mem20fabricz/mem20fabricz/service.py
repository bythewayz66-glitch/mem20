"""mem20fabricz service orchestration (assimilated)."""
from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict, List
from . import domain, ecosystem

class FabricService:
    def __init__(self):
        self._events: List[Dict[str, Any]] = []

    def status(self) -> Dict[str, Any]:
        st = domain.probe_members()
        rep = domain.summarize(st)
        out = asdict(rep)
        out["ok"] = rep.unavailable == 0
        out["absorbed_total"] = sum(1 for s in st if getattr(s, 'absorbed', False))
        return out

    def probe(self, include_signals: bool = False) -> Dict[str, Any]:
        st = domain.probe_members()
        plan = domain.dispatch_plan("integrate", {})
        signals = ecosystem.probe() if include_signals else {"skipped": True}
        rep = domain.summarize(st, plan=plan, signals=signals)
        self._events.append({"type": "probe", "members": rep.members, "importable": rep.importable})
        out = asdict(rep)
        if include_signals and isinstance(signals, dict):
            out["peer_surface_total"] = signals.get("peer_surface_total", signals.get("count", 0))
        return out

    def dispatch(self, intent: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        payload = payload or {}
        plan = domain.dispatch_plan(intent, payload)
        sig = {
            "api_gateway": ecosystem.api_gateway(payload),
            "integration_compiler": ecosystem.integration_compiler(payload.get("mapping") or {}),
            "episodic_traces": ecosystem.episodic_traces(f"dispatch:{intent}"),
            "event_autopilot": ecosystem.event_autopilot({"type": f"dispatch.{intent}", "intent": intent}),
            "team_radio": ecosystem.team_radio(f"dispatch {intent} -> {','.join(plan.selected[:2])}"),
            "dispatch_value": ecosystem.dispatch_value({"product": {"price": 100}, "customer": {"tier": "internal"}, "value": payload.get("value", 1000)}),
        }
        self._events.append({"type": "dispatch", "intent": intent, "selected": plan.selected})
        return {"ok": True, "plan": asdict(plan), "signals": sig, "events": len(self._events)}

    def doctor(self) -> Dict[str, Any]:
        st = domain.probe_members()
        sig = ecosystem.probe()
        plan = domain.dispatch_plan("health", {})
        return {
            "ok": True,
            "members": {"total": len(st), "importable": sum(1 for s in st if s.importable), "absorbed": sum(1 for s in st if getattr(s,'absorbed',False))},
            "peers": sig,
            "peer_surface_total": sig.get("peer_surface_total", sig.get("count", 0)),
            "sample_plan": asdict(plan),
        }
