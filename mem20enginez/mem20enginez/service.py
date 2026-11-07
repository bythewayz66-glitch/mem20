"""Crew runtime service: member registry/probing, plans, dispatch signals, state."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence
import uuid

from . import domain, ecosystem
from .store import ConflictError, NotFoundError, RuntimeStore


class ValidationError(ValueError):
    pass


class EngineRuntimeService:
    def __init__(self, db_path, estate_root: Optional[str] = None):
        self.store = RuntimeStore(db_path)
        self.estate_root = Path(estate_root) if estate_root else domain.ESTATE_ROOT

    def members(self) -> Dict[str, Any]:
        statuses = [domain.check_member(n, self.estate_root) for n in domain.MEMBERS]
        report = domain.summarize(statuses)
        compat = ecosystem.compat_probe()
        proto = ecosystem.protocol_discovery()
        return {"ok": report.ok, "report": report.to_dict(), "registry": [m.to_dict() for m in domain.member_registry()],
                "signals": {"runtime_compatibility": compat, "protocol_autodiscovery": proto}}

    def status(self) -> Dict[str, Any]:
        mem = self.members()
        lifecycle = ecosystem.runtime_lifecycle([{"id": "enginez", "stage": "active", "mrr": 1, "age_months": 1}])
        bundle = ecosystem.capability_bundle()
        return {"ok": True, "crew": "mem20enginez", "version": "1.0.0",
                "members_total": len(domain.MEMBERS), "members_present": mem["report"]["members_present"],
                "members_healthy": mem["report"]["members_healthy"], "metrics": self.store.metrics(),
                "signals": {"runtime_lifecycle": lifecycle, "service_bundling": bundle,
                            "runtime_compatibility": mem["signals"]["runtime_compatibility"],
                            "protocol_autodiscovery": mem["signals"]["protocol_autodiscovery"]}}

    def doctor(self) -> Dict[str, Any]:
        probe = ecosystem.probe()
        mem = self.members()
        return {"ok": probe.get("ok") and mem.get("ok"), "probe": probe,
                "members": {"total": len(domain.MEMBERS), "present": mem["report"]["members_present"], "healthy": mem["report"]["members_healthy"]},
                "metrics": self.store.metrics()}

    def plan(self, intent: str, context: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        intent = str(intent or "").strip()
        if not intent:
            raise ValidationError("intent required")
        statuses = [domain.check_member(n, self.estate_root) for n in domain.MEMBERS]
        plan = domain.dispatch_plan(intent, statuses, context)
        compat = domain.compatibility()
        spec = ecosystem.speculative_plan({"id": "dispatch", "intent": intent}, [s["member"] for s in plan.steps] or ["fallback"])
        pred = ecosystem.predictive_routing(history=plan.selected, candidates=list(domain.MEMBERS))
        bundle = ecosystem.capability_bundle([{"name": f"dispatch:{m}", "price": 1} for m in plan.selected] or [{"name": "dispatch:fallback", "price": 1}])
        lifecycle = ecosystem.runtime_lifecycle([{"id": plan.plan_id, "stage": "active", "mrr": len(plan.selected)}])
        payload = plan.to_dict()
        self.store.save_plan(payload)
        self.store.record_run(plan.plan_id, "planned", {"intent": intent, "selected": plan.selected})
        return {"ok": True, "plan": payload, "compatibility": compat,
                "signals": {"speculative_workflow": spec, "predictive_recall": pred, "service_bundling": bundle, "runtime_lifecycle": lifecycle}}

    def execute(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        payload = payload or {}
        intent = payload.get("intent") or payload.get("action") or ""
        if intent:
            return self.plan(str(intent), payload)
        return self.status()

    def plans(self, limit=50): return self.store.list_plans(limit)
    def get_plan(self, plan_id): return self.store.get_plan(plan_id)
    def runs(self, limit=100): return self.store.runs(limit)
    def events(self, since=0, limit=200): return self.store.events(since, limit)
    def snapshot(self, label=""): return {"ok": True, **self.store.snapshot(label)}
    def restore(self, snapshot_id): return self.store.restore(snapshot_id)

    def simulate(self) -> Dict[str, Any]:
        scenarios = {}
        statuses = [domain.check_member(n, self.estate_root) for n in domain.MEMBERS]
        rep = domain.summarize(statuses)
        scenarios["member_registry"] = {"ok": rep.members_total == 30 and rep.members_present >= 1, "total": rep.members_total, "present": rep.members_present, "healthy": rep.members_healthy}
        plan = domain.dispatch_plan("protocol compatibility speculative dispatch", statuses)
        scenarios["dispatch_plan"] = {"ok": bool(plan.plan_id) and isinstance(plan.steps, list), "selected": plan.selected}
        compat = ecosystem.compat_probe()
        proto = ecosystem.protocol_discovery()
        spec = ecosystem.speculative_plan()
        bundle = ecosystem.capability_bundle()
        pred = ecosystem.predictive_routing()
        life = ecosystem.runtime_lifecycle()
        probe = ecosystem.probe()
        scenarios["runtime_compatibility"] = {"ok": compat["ok"]}
        scenarios["protocol_autodiscovery"] = {"ok": proto["ok"]}
        scenarios["speculative_workflow"] = {"ok": spec["ok"]}
        scenarios["service_bundling"] = {"ok": bundle["ok"]}
        scenarios["predictive_recall"] = {"ok": pred["ok"]}
        scenarios["runtime_lifecycle"] = {"ok": life["ok"]}
        scenarios["peer_probe"] = {"ok": probe["ok"], "count": probe["count"]}
        passed = sum(1 for v in scenarios.values() if v.get("ok"))
        return {"ok": passed == len(scenarios), "passed": passed, "total": len(scenarios), "scenarios": scenarios}

    def benchmark(self, iterations=20) -> Dict[str, Any]:
        import time as _t
        statuses = [domain.check_member(n, self.estate_root) for n in domain.MEMBERS[:10]]
        t0 = _t.perf_counter()
        for _ in range(max(1, int(iterations))):
            domain.dispatch_plan("compat protocol", statuses)
            domain.summarize(statuses)
        dt = max(1e-9, _t.perf_counter() - t0)
        return {"ok": True, "iterations": int(iterations), "elapsed_s": round(dt, 6), "ops_per_sec": round(int(iterations) / dt, 3)}
