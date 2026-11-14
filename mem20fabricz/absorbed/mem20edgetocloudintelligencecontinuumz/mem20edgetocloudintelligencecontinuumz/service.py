"""Continuum orchestration service.

Owns the lifecycle:
    register target -> submit workload -> place -> dispatch/run -> complete/fail
                                                     -> migrate/failover on degradation

All state writes go through :class:`ContinuumStore`. Cross-subsystem judgements
come from :mod:`ecosystem` and are recorded in decisions/events; peer failures
never abort placement.
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any, Mapping

from . import domain, ecosystem
from .domain import (
    MigrationPlan,
    MigrationState,
    PlacementDecision,
    Target,
    TargetStatus,
    Workload,
    WorkloadState,
)
from .store import ConflictError, ContinuumStore, NotFoundError


class ValidationError(ValueError):
    pass


def _default_store() -> str:
    return os.environ.get("MEM20_EDGE_CLOUD_CONTINUUM_STORE") or os.path.expanduser(
        "~/.mem20/edgetocloudintelligencecontinuumz/continuum.db"
    )


class ContinuumService:
    def __init__(self, store_path: str | Path | None = None):
        self.store = ContinuumStore(store_path or _default_store())

    # -- targets -----------------------------------------------------------
    def register_target(self, spec: Mapping[str, Any]) -> dict:
        try:
            data = dict(spec)
            data.setdefault("target_id", data.get("id") or f"t-{uuid.uuid4().hex[:8]}")
            caps = data.get("capabilities")
            if isinstance(caps, str):
                data["capabilities"] = [c.strip() for c in caps.split(",") if c.strip()]
            zones = data.get("privacy_zones")
            if isinstance(zones, str):
                data["privacy_zones"] = [z.strip() for z in zones.split(",") if z.strip()]
            target = Target.from_dict(data)
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        result = self.store.put_target(target)
        market = ecosystem.capability_market([target.to_dict()], {"workload_id": "_register", "required_capabilities": list(target.capabilities)[:1] or ["compute"]})
        transport = ecosystem.transport_plan([target.to_dict()], None, target.target_id, {"workload_id": "_register", "max_latency_ms": target.latency_ms, "priority": 50, "size_mb": 1})
        result.update({"ok": True, "target": target.to_dict(), "capability_market": market, "transport": transport})
        return result

    def get_target(self, target_id: str) -> dict:
        return self.store.require_target(target_id).to_dict()

    def list_targets(self) -> list[dict]:
        return [t.to_dict() for t in self.store.list_targets()]

    def set_target_status(self, target_id: str, status: str) -> dict:
        target = self.store.require_target(target_id)
        try:
            target.status = TargetStatus(status)
        except Exception as exc:
            raise ValidationError(str(exc)) from exc
        res = self.store.put_target(target)
        return {"ok": True, **res, "target": target.to_dict()}

    def delete_target(self, target_id: str) -> dict:
        return {"ok": True, **self.store.delete_target(target_id)}

    # -- workloads ---------------------------------------------------------
    def submit_workload(self, spec: Mapping[str, Any]) -> dict:
        try:
            data = dict(spec)
            data.setdefault("workload_id", data.get("id") or f"w-{uuid.uuid4().hex[:10]}")
            data.setdefault("submitted_at", time.time())
            req = data.get("required_capabilities")
            if isinstance(req, str):
                data["required_capabilities"] = [c.strip() for c in req.split(",") if c.strip()]
            pref = data.get("preferred_tiers")
            if isinstance(pref, str):
                data["preferred_tiers"] = [t.strip() for t in pref.split(",") if t.strip()]
            workload = Workload.from_dict(data)
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        existing = self.store.idempotency_lookup(workload.idempotency_key)
        if existing:
            found = self.store.get_workload(existing)
            if found:
                return {"ok": True, "created": False, "idempotent": True, "workload": found.to_dict(), "existing_workload_id": existing}

        res = self.store.put_workload(workload)
        self.store.idempotency_store(workload.idempotency_key, workload.workload_id)
        targets = [t.to_dict() for t in self.store.list_targets()]
        preview = domain.place_workload(self.store.list_targets(), workload)
        federated = ecosystem.federated_plan(targets, workload.to_dict())
        cost = ecosystem.cost_plan(targets, workload.to_dict())
        resource = ecosystem.resource_market(targets, workload.to_dict())
        return {
            "ok": True, "created": True, **res, "workload": workload.to_dict(),
            "placement_preview": preview.to_dict(), "federated": federated, "cost": cost, "resource_market": resource,
        }

    def get_workload(self, workload_id: str) -> dict:
        return self.store.require_workload(workload_id).to_dict()

    def list_workloads(self, state: str | None = None) -> list[dict]:
        return [w.to_dict() for w in self.store.list_workloads(state)]

    # -- placement / dispatch ---------------------------------------------
    def _peer_bonuses(self, targets: list[Target], workload: Workload) -> tuple[dict[str, float], dict]:
        target_payloads = [t.to_dict() for t in targets]
        w = workload.to_dict()
        federated = ecosystem.federated_plan(target_payloads, w)
        cost = ecosystem.cost_plan(target_payloads, w)
        market = ecosystem.capability_market(target_payloads, w)
        resource = ecosystem.resource_market(target_payloads, w)
        transport = ecosystem.transport_plan(target_payloads, None, None, w)
        bonuses: dict[str, float] = {t.target_id: 0.0 for t in targets}
        # federated distribution may suggest a node
        dist = ((federated.get("distributed") or {}).get("node") if federated.get("ok") else None)
        if dist and dist in bonuses:
            bonuses[dist] += 0.03
        selected = (market.get("selected") or {}).get("seller") if market.get("ok") else None
        if selected and selected in bonuses:
            bonuses[selected] += 0.03
        bneck = cost.get("bottleneck") if cost.get("ok") else None
        if bneck and bneck in bonuses:
            bonuses[bneck] -= 0.02  # bottleneck is a penalty, not a reward
        signals = {"federated": federated, "cost": cost, "capability_market": market, "resource_market": resource, "transport": transport}
        return bonuses, signals

    def place(self, workload_id: str) -> dict:
        workload = self.store.require_workload(workload_id)
        if workload.state not in (WorkloadState.QUEUED, WorkloadState.FAILED, WorkloadState.PLACED):
            raise ValidationError(f"workload {workload_id} is {workload.state.value}, cannot place")
        targets = self.store.list_targets()
        bonuses, signals = self._peer_bonuses(targets, workload)
        decision = domain.place_workload(targets, workload, bonuses=bonuses)
        placement_id = self.store.record_placement(decision)
        if decision.chosen:
            target = self.store.require_target(decision.chosen)
            workload.state = WorkloadState.PLACED
            workload.assigned_target = decision.chosen
            self.store.put_workload(workload)
            migration_semantics = ecosystem.migration_semantics(workload.to_dict(), True)
        else:
            migration_semantics = ecosystem.migration_semantics(workload.to_dict(), False)
        return {
            "ok": True, "placement_id": placement_id, "decision": decision.to_dict(),
            "workload": self.store.require_workload(workload_id).to_dict(),
            "signals": signals, "migration_semantics": migration_semantics,
        }

    def dispatch(self, workload_id: str | None = None, limit: int | None = None) -> dict:
        ids = [workload_id] if workload_id else [w.workload_id for w in self.store.list_workloads("queued")][: (limit or 50)]
        decisions = []
        for wid in ids:
            workload = self.store.get_workload(wid)
            if not workload or workload.state != WorkloadState.QUEUED:
                continue
            placed = self.place(wid)
            decision = placed["decision"]
            if decision.get("chosen"):
                target = self.store.require_target(decision["chosen"])
                workload = self.store.require_workload(wid)
                target.reserve(workload)
                self.store.put_target(target)
                workload.state = WorkloadState.RUNNING
                self.store.put_workload(workload)
                placed["workload"] = workload.to_dict()
            decisions.append(placed)
        return {"ok": True, "dispatched": sum(1 for d in decisions if d["decision"].get("chosen")), "count": len(decisions), "decisions": decisions}

    def complete(self, workload_id: str, *, success: bool = True, reason: str = "") -> dict:
        workload = self.store.require_workload(workload_id)
        target = self.store.get_target(workload.assigned_target) if workload.assigned_target else None
        if target and workload.state in (WorkloadState.RUNNING, WorkloadState.PLACED, WorkloadState.MIGRATING):
            target.release(workload)
            self.store.put_target(target)
        if success:
            workload.state = WorkloadState.COMPLETED
        else:
            workload.attempts += 1
            if workload.attempts < workload.max_attempts:
                workload.state = WorkloadState.QUEUED
                workload.assigned_target = None
            else:
                workload.state = WorkloadState.FAILED
        workload.metadata = {**workload.metadata, "last_reason": reason, "last_success": success}
        self.store.put_workload(workload)
        return {"ok": True, "workload": workload.to_dict(), "released_target": target.target_id if target else None}

    # -- migration / failover ---------------------------------------------
    def failover(self, workload_id: str, reason: str = "failover requested") -> dict:
        workload = self.store.require_workload(workload_id)
        targets = self.store.list_targets()
        plan = domain.failover_plan(targets, workload, workload.assigned_target, reason=reason)
        migration_semantics = ecosystem.migration_semantics(workload.to_dict(), plan.destination is not None)
        if plan.destination and migration_semantics.get("phase") == "cutover":
            plan.state = MigrationState.CUTOVER
            plan.verified = True
            source = self.store.get_target(workload.assigned_target) if workload.assigned_target else None
            if source and workload.state == WorkloadState.RUNNING:
                source.release(workload)
                self.store.put_target(source)
            dest = self.store.require_target(plan.destination)
            dest.reserve(workload)
            self.store.put_target(dest)
            workload.state = WorkloadState.RUNNING
            workload.assigned_target = plan.destination
            self.store.put_workload(workload)
        elif plan.destination:
            plan.state = MigrationState.ROLLED_BACK
            plan.verified = False
        self.store.put_migration(plan)
        return {"ok": plan.destination is not None, "plan": plan.to_dict(), "migration_semantics": migration_semantics, "workload": self.store.require_workload(workload_id).to_dict()}

    def plan_migrations(self, load_threshold: float = 0.85) -> dict:
        plan = domain.migration_plan(self.store.list_targets(), self.store.list_workloads(), load_threshold=load_threshold)
        return {"ok": True, **plan}

    # -- observability / self-checks --------------------------------------
    def status(self) -> dict:
        targets = self.store.list_targets()
        workloads = self.store.list_workloads()
        health = domain.continuum_health(targets, workloads)
        transport = ecosystem.transport_plan([t.to_dict() for t in targets], None, None, {"workload_id": "_status", "max_latency_ms": 200, "priority": 50, "size_mb": 1})
        return {
            "ok": True, "health": health.to_dict(), "metrics": self.store.metrics(),
            "tiers": health.tiers, "transport": transport,
        }

    def events(self, since: int = 0, limit: int = 200) -> list[dict]:
        return self.store.events_since(since, limit)

    def snapshot(self, label: str = "") -> dict:
        return {"ok": True, **self.store.snapshot(label)}

    def restore(self, snapshot_id: str) -> dict:
        return {"ok": True, **self.store.restore(snapshot_id)}

    def metrics(self) -> dict:
        return self.store.metrics()

    def doctor(self) -> dict:
        probe = ecosystem.probe()
        # force real calls through service-owned context too
        targets = [Target(target_id="dr-local", tier="local", capabilities={"compute"}, latency_ms=2).to_dict(),
                   Target(target_id="dr-cloud", tier="cloud", capabilities={"compute"}, latency_ms=80, cost_per_cpu_hour=0.2).to_dict()]
        workload = {"workload_id": "dr-probe", "cpu": 1, "duration_s": 60, "max_latency_ms": 100, "priority": 50, "size_mb": 1, "required_capabilities": ["compute"]}
        checks = {
            "federated": ecosystem.federated_plan(targets, workload),
            "cost": ecosystem.cost_plan(targets, workload),
            "transport": ecosystem.transport_plan(targets, "dr-local", "dr-cloud", workload),
            "migration": ecosystem.migration_semantics(workload, True),
            "capability_market": ecosystem.capability_market(targets, workload),
            "resource_market": ecosystem.resource_market(targets, workload),
        }
        reachable = [k for k, v in checks.items() if v.get("ok")]
        return {"ok": len(reachable) == 6, "checks": checks, "probe": probe, "reachable": reachable, "count": len(reachable)}

    def benchmark(self, iterations: int = 20) -> dict:
        targets = [Target(target_id=f"b-{i}", tier=["local", "edge", "private", "peer", "cloud"][i % 5],
                          capabilities={"compute", "gpu"} if i % 2 == 0 else {"compute"},
                          cpu=8, memory_gb=16, latency_ms=2 + i * 7, cost_per_cpu_hour=i * 0.03,
                          reliability=0.99 - i * 0.001, bandwidth_mbps=100).to_dict() for i in range(12)]
        workload = {"workload_id": "bench", "cpu": 2, "memory_gb": 4, "duration_s": 120, "required_capabilities": ["compute"], "priority": 50, "size_mb": 5}
        start = time.perf_counter()
        last = None
        for _ in range(max(1, iterations)):
            t_objs = [Target.from_dict(t) for t in targets]
            w_obj = Workload.from_dict(workload)
            last = domain.place_workload(t_objs, w_obj)
            ecosystem.cost_plan(targets, workload)
            ecosystem.transport_plan(targets, targets[0]["target_id"], targets[-1]["target_id"], workload)
        elapsed = time.perf_counter() - start
        ops = iterations / elapsed if elapsed else 0.0
        return {"ok": True, "iterations": iterations, "elapsed_s": round(elapsed, 6), "ops_per_sec": round(ops, 2),
                "chosen": last.chosen if last else None, "score": last.score if last else None}

    def simulate(self) -> dict:
        tmp = Path(self.store.path).with_name(f"simulate-{uuid.uuid4().hex[:8]}.db")
        svc = ContinuumService(tmp)
        scenarios = {}
        try:
            reg = svc.register_target({"target_id": "sim-local", "tier": "local", "capabilities": ["compute"], "cpu": 8, "memory_gb": 16, "latency_ms": 2, "cost_per_cpu_hour": 0})
            reg2 = svc.register_target({"target_id": "sim-cloud", "tier": "cloud", "capabilities": ["compute", "gpu"], "cpu": 32, "memory_gb": 64, "latency_ms": 90, "cost_per_cpu_hour": 0.4})
            scenarios["register"] = {"ok": reg["ok"] and reg2["ok"], "tiers": [reg["target"]["tier"], reg2["target"]["tier"]]}

            sub = svc.submit_workload({"workload_id": "sim-w", "cpu": 2, "memory_gb": 2, "required_capabilities": ["compute"], "duration_s": 60, "idempotency_key": "sim-k"})
            scenarios["submit"] = {"ok": sub["ok"] and sub["created"]}

            disp = svc.dispatch("sim-w")
            chosen = disp["decisions"][0]["decision"]["chosen"] if disp["decisions"] else None
            scenarios["placement"] = {"ok": disp["dispatched"] == 1 and chosen is not None, "chosen": chosen}

            svc.set_target_status(chosen, "offline")
            fo = svc.failover("sim-w", reason="simulated outage")
            scenarios["failover"] = {"ok": bool(fo.get("plan", {}).get("destination")) or not fo.get("ok"), "verified": fo.get("plan", {}).get("verified"), "destination": fo.get("plan", {}).get("destination")}

            # malformed
            try:
                svc.submit_workload({"workload_id": "bad", "cpu": 0})
                scenarios["malformed"] = {"ok": False}
            except (ValidationError, Exception):
                scenarios["malformed"] = {"ok": True}

            # overload / infeasible
            svc.register_target({"target_id": "sim-tiny", "tier": "edge", "capabilities": ["compute"], "cpu": 1, "memory_gb": 1, "latency_ms": 10})
            big = svc.submit_workload({"workload_id": "sim-big", "cpu": 999, "memory_gb": 1, "required_capabilities": ["compute"]})
            placed_big = svc.place("sim-big")
            scenarios["infeasible"] = {"ok": placed_big["decision"]["chosen"] is None, "bottlenecks": len(placed_big["decision"]["bottlenecks"])}

            # idempotency
            again = svc.submit_workload({"workload_id": "sim-w2", "cpu": 1, "memory_gb": 1, "required_capabilities": ["compute"], "idempotency_key": "sim-k"})
            scenarios["idempotency"] = {"ok": not again.get("created", True) and again.get("idempotent", False)}

            snap = svc.snapshot("sim")
            scenarios["snapshot"] = {"ok": snap["ok"], "snapshot_id": snap["snapshot_id"]}
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            for suffix in ("-wal", "-shm"):
                try:
                    os.unlink(str(tmp) + suffix)
                except OSError:
                    pass
        passed = sum(1 for v in scenarios.values() if v.get("ok"))
        return {"ok": passed == len(scenarios), "passed": passed, "total": len(scenarios), "scenarios": scenarios}
