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
        compat = ecosystem.compat_probe()
        proto = ecosystem.protocol_discovery()
        bundle = ecosystem.capability_bundle()
        peer_probe = ecosystem.probe(include_member_ecosystems=True)
        return {
            "ok": mem["ok"],
            "subsystem": "mem20enginez",
            "members_total": mem["report"]["members_total"],
            "members_present": mem["report"]["members_present"],
            "members_importable": mem["report"]["members_importable"],
            "absorbed_total": mem["report"].get("absorbed_total", 0),
            "peer_surface_total": peer_probe.get("peer_surface_total", peer_probe.get("count", 0)),
            "signals": {
                "runtime_compatibility": compat,
                "protocol_autodiscovery": proto,
                "runtime_lifecycle": lifecycle,
                "service_bundling": bundle,
            },
            "peers": peer_probe,
            "metrics": self.store.metrics(),
        }

    def plan(self, intent: str, context: Mapping[str, Any] = None) -> Dict[str, Any]:
        if not intent or not str(intent).strip():
            raise ValidationError("intent required")
        statuses = [domain.check_member(n, self.estate_root) for n in domain.MEMBERS]
        plan = domain.dispatch_plan(str(intent), statuses)
        plan.signals.update({"context_keys": sorted(list((context or {}).keys()))})
        pred = ecosystem.predictive_routing(candidates=plan.members[:8])
        spec = ecosystem.speculative_plan({"id": plan.plan_id, "intent": intent, "steps": [s["member"] for s in plan.steps]})
        bundle = ecosystem.capability_bundle([{"name": m, "price": 1} for m in plan.members[:5]])
        lifecycle = ecosystem.runtime_lifecycle([{"id": m, "stage": "active"} for m in plan.members[:3]])
        signals = {"predictive_recall": pred, "speculative_workflow": spec, "service_bundling": bundle, "runtime_lifecycle": lifecycle}
        payload = plan.to_dict()
        payload["signals"].update(signals)
        self.store.save_plan(payload)
        return {"ok": True, "plan": payload, "signals": signals}

    def dispatch(self, intent_or_plan: Any, payload: Mapping[str, Any] = None) -> Dict[str, Any]:
        payload = dict(payload or {})
        if isinstance(intent_or_plan, Mapping) and intent_or_plan.get("plan_id"):
            plan = dict(intent_or_plan)
        elif isinstance(intent_or_plan, str) and intent_or_plan.strip():
            plan = self.plan(intent_or_plan, payload)["plan"]
        else:
            raise ValidationError("intent or plan required")
        run = self.store.record_run(plan.get("plan_id"), "dispatched", {"intent": plan.get("intent"), "members": plan.get("members", [])})
        return {"ok": True, "plan_id": plan.get("plan_id"), "run": run, "dispatched_members": plan.get("members", [])}

    def doctor(self) -> Dict[str, Any]:
        probe = ecosystem.probe(include_member_ecosystems=True)
        statuses = [domain.check_member(n, self.estate_root) for n in domain.MEMBERS]
        report = domain.summarize(statuses)
        return {"ok": probe.get("ok", False) and report.ok, "probe": probe, "members": report.to_dict(), "store": self.store.metrics()}

    def simulate(self) -> Dict[str, Any]:
        steps = []
        # 1) members
        m = self.members()
        steps.append({"name": "members", "ok": bool(m.get("report", {}).get("members_total", 0) > 0)})
        # 2) core probes
        for name, fn in [("compat", ecosystem.compat_probe), ("proto", ecosystem.protocol_discovery), ("spec", ecosystem.speculative_plan),
                         ("bundle", ecosystem.capability_bundle), ("predict", ecosystem.predictive_routing), ("lifecycle", ecosystem.runtime_lifecycle)]:
            try:
                r = fn()
                steps.append({"name": name, "ok": bool(r.get("ok"))})
            except Exception as e:
                steps.append({"name": name, "ok": False, "error": f"{type(e).__name__}: {e}"})
        # 3) plan + dispatch
        try:
            p = self.plan("simulate dispatch compatibility protocol")
            d = self.dispatch(p["plan"])
            steps.append({"name": "plan_dispatch", "ok": bool(p.get("ok") and d.get("ok"))})
        except Exception as e:
            steps.append({"name": "plan_dispatch", "ok": False, "error": str(e)})
        # 4) absorbed member ecosystem aggregation
        try:
            agg = ecosystem.absorbed_member_peers()
            steps.append({"name": "absorbed_member_peers", "ok": bool(agg.get("ok") and agg.get("peer_checks_total", 0) >= 0)})
        except Exception as e:
            steps.append({"name": "absorbed_member_peers", "ok": False, "error": str(e)})
        passed = sum(1 for s in steps if s.get("ok"))
        return {"ok": passed == len(steps), "passed": passed, "total": len(steps), "steps": steps}

    # state ops
    def put(self, kind, ident, payload, expected_version=None):
        return self.store.put(kind, ident, payload, expected_version=expected_version)

    def get(self, kind, ident):
        return self.store.get(kind, ident)

    def list(self, kind=None):
        return self.store.list(kind)

    def delete(self, kind, ident):
        return self.store.delete(kind, ident)

    def events(self, since=0):
        return self.store.events(since=since)

    def snapshot(self, label=""):
        return self.store.snapshot(label)

    def restore(self, snapshot_id):
        return self.store.restore(snapshot_id)


    # compatibility helpers
    def plans(self, limit=50):
        return self.store.list_plans(limit)

    def get_plan(self, plan_id):
        p = self.store.get_plan(plan_id)
        if not p:
            raise NotFoundError(f"plan not found: {plan_id}")
        return p

    def runs(self, limit=100):
        return self.store.runs(limit)

    def events(self, since=0, limit=200):
        return self.store.events(since=since, limit=limit)

    def execute(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError("payload must be an object")
        intent = payload.get("intent") or ""
        if payload.get("plan_id"):
            plan = self.get_plan(payload["plan_id"])
        elif intent:
            plan = self.plan(intent, payload.get("context") or {}).get("plan")
        else:
            raise ValidationError("intent or plan_id required")
        return self.dispatch(plan, payload)

    def benchmark(self, iterations=20):
        import time as _time
        it = max(1, int(iterations))
        t0 = _time.perf_counter()
        ok = 0
        for i in range(it):
            p = self.plan(f"benchmark-{i}", {})
            if p.get("ok"): ok += 1
        dt = _time.perf_counter() - t0
        return {"ok": True, "iterations": it, "successful": ok, "elapsed_s": round(dt, 6), "per_iter_ms": round((dt/it)*1000, 4)}
