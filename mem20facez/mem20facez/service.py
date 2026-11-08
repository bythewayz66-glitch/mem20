"""mem20facez service orchestration (#312): durable composition lifecycle."""
from __future__ import annotations

import concurrent.futures
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from . import domain, ecosystem
from .store import FacezStore


class ValidationError(ValueError):
    pass


def _signal_assertable(sig: Dict[str, Any]) -> bool:
    return isinstance(sig, dict) and "subsystem" in sig and "ok" in sig


class FacezService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or Path("state") / "mem20facez.sqlite3")
        self.store = FacezStore(self.db_path)

    def status(self) -> Dict[str, Any]:
        st = domain.probe_members()
        imp = sum(1 for s in st if s.importable)
        return {"ok": imp == len(st), "members": len(st), "importable": imp, "statuses": [asdict(s) for s in st], "durable": self.store.metrics()}

    def _validate_compose(self, intent: Any, payload: Any) -> Dict[str, Any]:
        if intent is None or not str(intent).strip():
            raise ValidationError("intent must be a non-empty string")
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise ValidationError("payload must be an object")
        return payload

    def _run_step(self, name: str, fn):
        t0 = time.time()
        try:
            result = fn()
            ok = bool(result.get("ok")) if isinstance(result, dict) else True
            return {"step": name, "ok": ok, "status": "completed" if ok else "failed", "result": result, "error": result.get("error") if isinstance(result, dict) else None, "duration_ms": round((time.time() - t0) * 1000, 3)}
        except Exception as e:
            return {"step": name, "ok": False, "status": "failed", "result": None, "error": f"{type(e).__name__}: {e}", "duration_ms": round((time.time() - t0) * 1000, 3)}

    def _execute_composition(self, intent: str, payload: Dict[str, Any], plan, composition_id: str) -> Dict[str, Any]:
        step_defs = [
            ("multimodal_capture", lambda: ecosystem.multimodal_capture(payload)),
            ("dataflow_compose", lambda: ecosystem.dataflow_compose(payload)),
            ("mission_compile", lambda: ecosystem.mission_compile(intent)),
            ("automation_canvas", lambda: ecosystem.automation_canvas(payload)),
            ("sandbox_world", lambda: ecosystem.sandbox_world(payload)),
            ("agent_blackboard", lambda: ecosystem.agent_blackboard(payload)),
        ]
        steps = []
        outputs = {}
        errors = []
        for name, fn in step_defs:
            self.store.event(composition_id, "step.started", {"step": name})
            step = self._run_step(name, fn)
            steps.append(step)
            outputs[name] = step["result"]
            self.store.event(composition_id, "step.finished", {"step": name, "ok": step["ok"], "error": step.get("error")})
            if not step["ok"]:
                errors.append({"step": name, "error": step.get("error"), "action": "safe_degradation"})
                # retry once for transient-looking failures
                if "Timeout" in str(step.get("error") or ""):
                    self.store.event(composition_id, "step.retry", {"step": name})
                    retry = self._run_step(name, fn)
                    retry["retried"] = True
                    steps[-1] = retry
                    outputs[name] = retry["result"]
                    self.store.event(composition_id, "step.retry_finished", {"step": name, "ok": retry["ok"], "error": retry.get("error")})
                    if retry["ok"]:
                        errors = [e for e in errors if e["step"] != name]
                    else:
                        errors[-1]["retry_error"] = retry.get("error")
        return {"steps": steps, "outputs": outputs, "errors": errors}

    def compose(self, intent: str = "workspace", payload: Dict[str, Any] = None, composition_id: Optional[str] = None, safe_degrade: bool = True) -> Dict[str, Any]:
        payload = self._validate_compose(intent, payload or {})
        intent = str(intent)
        plan = domain.compose_plan(intent, payload)
        cid = str(composition_id or f"facez-{uuid.uuid4().hex[:16]}")
        comp = {
            "composition_id": cid,
            "status": "planned",
            "intent": intent,
            "payload": payload,
            "plan": asdict(plan),
            "steps": [],
            "outputs": {},
            "errors": [],
        }
        comp = self.store.put(comp)
        self.store.event(cid, "composition.validated", {"intent": intent})
        comp["status"] = "running"
        comp = self.store.put(comp, expected_version=comp["version"])
        exec_result = self._execute_composition(intent, payload, plan, cid)
        comp["steps"] = exec_result["steps"]
        comp["outputs"] = exec_result["outputs"]
        comp["errors"] = exec_result["errors"]
        failed = [s for s in comp["steps"] if not s.get("ok")]
        if not failed:
            comp["status"] = "completed"
        elif len(failed) < len(comp["steps"]) and safe_degrade:
            comp["status"] = "partial"
        else:
            comp["status"] = "failed"
        comp = self.store.put(comp, expected_version=comp["version"])
        self.store.event(cid, "composition.finished", {"status": comp["status"], "failed_steps": [s["step"] for s in failed]})
        signals = {s["step"]: (s.get("result") if isinstance(s.get("result"), dict) else {"ok": s.get("ok"), "value": s.get("result")}) for s in comp["steps"]}
        return {
            "ok": comp["status"] in ("completed", "partial"),
            "status": comp["status"],
            "composition_id": cid,
            "version": comp["version"],
            "plan": comp["plan"],
            "steps": comp["steps"],
            "signals": signals,
            "errors": comp["errors"],
            "partial_completion": comp["status"] == "partial",
            "durable": {"db": self.db_path, "history_count": len(self.store.history(cid))},
        }

    def get_composition(self, composition_id: str) -> Dict[str, Any]:
        c = self.store.get(composition_id)
        if not c:
            return {"ok": False, "error": "not_found", "composition_id": composition_id}
        return {"ok": True, "composition": c, "history": self.store.history(composition_id)}

    def rollback(self, composition_id: str, reason: str = "operator rollback") -> Dict[str, Any]:
        c = self.store.get(composition_id)
        if not c:
            return {"ok": False, "error": "not_found", "composition_id": composition_id}
        self.store.event(composition_id, "rollback.requested", {"reason": reason, "from_status": c["status"]})
        c["status"] = "rolled_back"
        c["errors"] = list(c.get("errors") or []) + [{"action": "rollback", "reason": reason, "ts": time.time()}]
        c = self.store.put(c, expected_version=c["version"])
        self.store.event(composition_id, "rollback.completed", {"status": c["status"]})
        return {"ok": True, "composition": c}

    def recover(self, composition_id: str) -> Dict[str, Any]:
        payload = self.get_composition(composition_id)
        if not payload.get("ok"):
            return payload
        c = payload["composition"]
        if c["status"] in ("completed", "rolled_back"):
            return {"ok": True, "recovered": False, "composition": c, "reason": "terminal_state"}
        # safe recovery: re-run as a new versioned attempt from same intent/payload
        self.store.event(composition_id, "recover.requested", {"from_status": c["status"]})
        rerun = self.compose(c["intent"], c["payload"], composition_id=composition_id, safe_degrade=True)
        rerun["recovered"] = True
        return rerun

    def doctor(self) -> Dict[str, Any]:
        st = domain.probe_members()
        sig = ecosystem.probe()
        plan = domain.compose_plan("health", {})
        sample = None
        try:
            sample = {"composition_id": "probe-not-persisted", "plan": asdict(plan)}
        except Exception:
            sample = None
        return {"ok": True, "members": {"total": len(st), "importable": sum(1 for s in st if s.importable)}, "peers": sig, "sample_plan": asdict(plan), "durable": self.store.metrics()}
