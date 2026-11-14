"""Fleet orchestration service.

This is the layer that makes the subsystem a running part of mem20 rather than
a library of formulas. It owns the sequence:

    submit -> place -> reserve -> dispatch -> complete/fail -> evacuate/rebalance

and it is the only place that writes the state plane. Every important choice
returns a :class:`~mem20causalroutingbrainz.domain.PlacementDecision` with
alternatives, bottlenecks and confidence, all the
estate seam in :mod:`mem20causalroutingbrainz.ecosystem` so the placement is also a
swarm, energy, device-capability, hardware, roaming and sleep judgement.

Failure policy is explicit. A malformed submission raises ``ValueError`` before
anything is stored. A workload that cannot be placed stays ``queued`` and the
decision lists the bottlenecks. A node that disagrees with an expected version
raises ``ConflictError`` rather than silently winning a race. Nothing is
swallowed.
"""
from __future__ import annotations

import statistics
import tempfile
import time
import uuid
from pathlib import Path
from typing import Mapping

from . import domain, ecosystem
from .domain import Node, Workload, WorkloadState
from .store import FleetStore

__all__ = ["FleetService", "ValidationError"]


class ValidationError(ValueError):
    """Input does not describe a valid fleet object."""


_NODE_FIELDS = set(Node.__dataclass_fields__)
_WORKLOAD_FIELDS = set(Workload.__dataclass_fields__)


def _filtered(payload: Mapping, allowed: set, label: str) -> dict:
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValidationError(f"{label}: unknown field(s) {', '.join(unknown)}")
    return dict(payload)


class FleetService:
    """A capability-aware fleet scheduler with a persistent state plane."""

    def __init__(self, store_path: str | Path) -> None:
        self.store = FleetStore(store_path)

    # ------------------------------------------------------------------
    # nodes
    # ------------------------------------------------------------------
    def register_node(self, payload: Mapping, expected_version: int | None = None) -> dict:
        data = _filtered(payload, _NODE_FIELDS | {"auto_capabilities"}, "node")
        if not data.get("node_id"):
            raise ValidationError("node: node_id required")
        fit = None
        if data.pop("auto_capabilities", False):
            fit = ecosystem.device_fit(data)
            caps = set(data.get("capabilities") or ())
            if fit.get("ok"):
                if fit.get("can_run_ml"):
                    caps.add("ml")
                if fit.get("can_render_3d"):
                    caps.add("3d")
                caps.add(f"tier:{fit.get('tier')}")
            data["capabilities"] = caps
        try:
            node = Node.from_dict(data)
        except ValueError as exc:
            raise ValidationError(f"node: {exc}") from exc
        if node.last_seen == 0.0:
            node.last_seen = time.time()
        if fit is None:
            fit = ecosystem.device_fit(node.to_dict())
        peers = [peer.to_dict() for peer in self.store.list_nodes()]
        capacity = sorted(node.capabilities)[0] if node.capabilities else None
        admission = ecosystem.swarm_admission(
            node.to_dict(), peers=peers, capability=capacity,
            urgency=min(1.0, max(0.0, node.reliability)))
        quote = ecosystem.hardware_quote(node.to_dict(), listings=peers)
        stored = self.store.put_node(node, expected_version=expected_version)
        self.store.append_event("node.registered", {
            "node_id": node.node_id, "kind": node.kind.value,
            "capabilities": sorted(node.capabilities),
            "swarm_quorum": admission.get("quorum") if admission.get("ok") else None,
            "compatible": fit.get("compatible") if fit.get("ok") else None,
        })
        return {"ok": True, "node": node.to_dict(), **stored,
                "swarm": admission, "device": fit, "quote": quote}

    def list_nodes(self) -> list[dict]:
        return [node.to_dict() for node in self.store.list_nodes()]

    def get_node(self, node_id: str) -> dict:
        return self.store.require_node(node_id).to_dict()

    def delete_node(self, node_id: str, expected_version: int | None = None) -> dict:
        return self.store.delete_node(node_id, expected_version=expected_version)

    def set_node_status(self, node_id: str, status: str) -> dict:
        node = self.store.require_node(node_id)
        try:
            node.status = domain.NodeStatus(str(status))
        except ValueError as exc:
            raise ValidationError(
                f"node status: {status!r} is not one of "
                f"{[item.value for item in domain.NodeStatus]}") from exc
        node.last_seen = time.time()
        stored = self.store.put_node(node)
        self.store.append_event("node.status", {"node_id": node_id,
                                                "status": node.status.value})
        return {"ok": True, "node": node.to_dict(), **stored}

    # ------------------------------------------------------------------
    # workloads
    # ------------------------------------------------------------------
    def submit_workload(self, payload: Mapping) -> dict:
        data = _filtered(payload, _WORKLOAD_FIELDS, "workload")
        if not data.get("workload_id"):
            data["workload_id"] = "wl-" + uuid.uuid4().hex[:12]
        key = str(data.get("idempotency_key") or data["workload_id"])
        existing = self.store.lookup_key(key)
        if existing is not None:
            current = self.store.require_workload(existing)
            return {"ok": True, "created": False, "idempotent": True,
                    "workload": current.to_dict()}
        if data.get("submitted_at") in (None, 0.0):
            data["submitted_at"] = time.time()
        try:
            workload = Workload.from_dict(data)
        except ValueError as exc:
            raise ValidationError(f"workload: {exc}") from exc
        claimed = self.store.claim_key(key, workload.workload_id)
        if not claimed:
            current = self.store.require_workload(
                self.store.lookup_key(key) or workload.workload_id)
            return {"ok": True, "created": False, "idempotent": True,
                    "workload": current.to_dict()}
        stored = self.store.put_workload(workload)
        nodes = self.store.list_nodes()
        preview = ecosystem.roaming_plan(
            [workload.to_dict()], [node.to_dict() for node in nodes])
        fits = {
            node.node_id: ecosystem.device_fit(node.to_dict(),
                                               workload.required_capabilities)
            for node in nodes
        }
        compatible = sorted(node_id for node_id, fit in fits.items()
                            if fit.get("ok") and fit.get("compatible"))
        self.store.append_event("workload.submitted", {
            "workload_id": workload.workload_id,
            "priority": workload.priority,
            "required_capabilities": sorted(workload.required_capabilities),
            "preview_target": (preview.get("assignments") or [{}])[0].get("node")
            if preview.get("ok") and preview.get("assignments") else None,
            "compatible_nodes": len(compatible),
        })
        return {"ok": True, "created": True, "workload": workload.to_dict(),
                **stored, "roaming": preview, "compatible_nodes": compatible}

    def list_workloads(self, state: str | None = None) -> list[dict]:
        return [workload.to_dict() for workload in self.store.list_workloads(state)]

    def get_workload(self, workload_id: str) -> dict:
        return self.store.require_workload(workload_id).to_dict()

    # ------------------------------------------------------------------
    # dispatch
    # ------------------------------------------------------------------
    def dispatch(self, workload_id: str | None = None, limit: int | None = None) -> dict:
        """Place queued work, returning a decision per workload.

        ``workload_id`` dispatches one specific workload; otherwise queued work
        is ordered by priority (highest first) and then by submission time.
        """
        if workload_id is not None:
            candidates = [self.store.require_workload(workload_id)]
            if candidates[0].state is not WorkloadState.QUEUED:
                raise ValidationError(
                    f"workload {workload_id} is {candidates[0].state.value}, not queued")
        else:
            candidates = [w for w in self.store.list_workloads(WorkloadState.QUEUED)]
            candidates.sort(key=lambda w: (-w.priority, w.submitted_at, w.workload_id))
        if limit is not None:
            candidates = candidates[: max(0, int(limit))]

        decisions: list[dict] = []
        for workload in candidates:
            competing = len(candidates) - 1
            decisions.append(self._dispatch_one(workload, competing))
        return {"ok": True, "dispatched": sum(1 for d in decisions if d["placed"]),
                "decisions": decisions}

    def _apply_sleep_policy(self, nodes: list[Node], workload: Workload) -> tuple[dict, list[str], list[Node]]:
        """Let the sleep subsystem decide which idle nodes may hibernate.

        The sleep system owns the idle policy; the fleet only applies it. Two
        rules keep the policy from starving work:

        * high-priority work wakes every hibernating node, because paying the
          wake cost is cheaper than missing the deadline;
        * low-priority work may sleep idle nodes but never the last awake one,
          so a queued workload can still be placed.

        A node is left with its old ``last_seen`` while asleep, which is what
        makes the idle judgement idempotent: the sleep system keeps reporting
        it as idle until an explicit wake updates the activity timestamp.
        """
        sleep = ecosystem.sleep_plan([node.to_dict() for node in nodes])
        woken: list[str] = []
        if not sleep.get("ok"):
            return sleep, woken, nodes

        idle_ids = list(sleep.get("sleeping", []))
        already_sleeping = [n.node_id for n in nodes
                            if n.status is domain.NodeStatus.SLEEPING]
        candidates = list(dict.fromkeys(idle_ids + already_sleeping))

        if workload.priority >= 60:
            for node_id in candidates:
                node = self.store.get_node(node_id)
                if node is None or node.status is not domain.NodeStatus.SLEEPING:
                    continue
                node.status = domain.NodeStatus.ONLINE
                node.last_seen = time.time()
                self.store.put_node(node)
                woken.append(node_id)
            return sleep, woken, self.store.list_nodes()

        awake = [n for n in nodes
                 if n.status in (domain.NodeStatus.ONLINE, domain.NodeStatus.DEGRADED)]
        for node_id in idle_ids:
            if len(awake) <= 1:
                break
            node = next((n for n in awake if n.node_id == node_id), None)
            if node is None:
                continue
            node.status = domain.NodeStatus.SLEEPING
            self.store.put_node(node)
            awake.remove(node)
        return sleep, woken, self.store.list_nodes()

    def _dispatch_one(self, workload: Workload, competing: int) -> dict:
        nodes = self.store.list_nodes()

        # Energy-aware sleep: idle edge nodes are allowed to sleep, and only
        # high-priority work pays the cost of waking them again.
        sleep, woken, nodes = self._apply_sleep_policy(nodes, workload)

        energy = ecosystem.energy_plan(
            [node.to_dict() for node in nodes], workload.to_dict())
        roaming = ecosystem.roaming_plan(
            [workload.to_dict()], [node.to_dict() for node in nodes])

        bonuses: dict[str, float] = {}
        if energy.get("ok") and energy.get("greenest"):
            bonuses[energy["greenest"]] = bonuses.get(energy["greenest"], 0.0) + 0.06
        roaming_target = None
        if roaming.get("ok"):
            for assignment in roaming.get("assignments", []):
                if assignment.get("workload") == workload.workload_id:
                    roaming_target = assignment.get("node")
                    break
        if roaming_target:
            bonuses[roaming_target] = bonuses.get(roaming_target, 0.0) + 0.03

        remote_latency: dict[str, float] = {}
        federated_credit: dict[str, float] = {}
        for node in nodes:
            if node.region != "local":
                remote_latency[node.node_id] = node.latency_ms
                federated_credit[node.node_id] = 0.7 if node.reliability >= 0.9 else 0.4

        decision = domain.place_workload(
            nodes, workload,
            remote_latency=remote_latency,
            federated_credit=federated_credit,
            bonuses=bonuses,
        )
        self.store.record_placement(decision)

        result: dict = {
            "workload_id": workload.workload_id,
            "placed": decision.placed,
            "decision": decision.to_dict(),
            "energy": energy,
            "roaming": roaming,
            "sleep": sleep,
            "woken": woken,
            "cross_system_bonuses": bonuses,
            "competing": competing,
        }
        if not decision.placed:
            self.store.append_event("workload.unplaceable", {
                "workload_id": workload.workload_id,
                "bottlenecks": decision.bottlenecks,
                "energy_preferred": energy.get("greenest"),
            })
            return result

        node = self.store.require_node(decision.chosen)  # type: ignore[arg-type]
        node.reserve(workload)
        node.last_seen = time.time()
        self.store.put_node(node)
        workload.state = WorkloadState.RUNNING
        workload.assigned_node = node.node_id
        self.store.put_workload(workload)
        self.store.append_event("workload.dispatched", {
            "workload_id": workload.workload_id,
            "node_id": node.node_id,
            "score": decision.score,
            "confidence": decision.confidence,
            "energy_preferred": energy.get("greenest"),
            "roaming_preferred": roaming_target,
            "woken": woken,
        })
        result["chosen"] = node.to_dict()
        return result

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def complete(self, workload_id: str, success: bool = True,
                 reason: str = "") -> dict:
        workload = self.store.require_workload(workload_id)
        if workload.state is not WorkloadState.RUNNING:
            raise ValidationError(
                f"workload {workload_id} is {workload.state.value}, not running")
        if workload.assigned_node:
            node = self.store.get_node(workload.assigned_node)
            if node is not None:
                node.release(workload)
                if not success:
                    node.fault_count += 1
                node.last_seen = time.time()
                self.store.put_node(node)
        workload.state = WorkloadState.COMPLETED if success else WorkloadState.FAILED
        if not success and workload.retries < 3 and workload.tolerate_fault:
            # A failed workload that tolerates fault is re-queued exactly once
            # per retry slot; the attempt counter is persisted so a restart
            # cannot reset the budget.
            workload.retries += 1
            workload.state = WorkloadState.QUEUED
            workload.assigned_node = None
        stored = self.store.put_workload(workload)
        self.store.append_event("workload.finished", {
            "workload_id": workload_id, "state": workload.state.value,
            "success": success, "retries": workload.retries, "reason": reason,
        })
        return {"ok": True, "workload": workload.to_dict(), **stored}

    def drain_node(self, node_id: str) -> dict:
        """Stop accepting new work on a node and report what would move.

        Draining is reversible (``set_node_status`` back to ``online``); it does
        not itself move running work. ``evacuate`` is the destructive step and
        is separate on purpose.
        """
        node = self.store.require_node(node_id)
        node.status = domain.NodeStatus.DRAINING
        node.last_seen = time.time()
        stored = self.store.put_node(node)
        plan = domain.evacuation_plan(
            self.store.list_nodes(), self.store.list_workloads(), node_id)
        self.store.append_event("node.draining", {
            "node_id": node_id, "moves": len(plan["moves"]),
            "stranded": len(plan["stranded"]),
        })
        return {"ok": True, "node": node.to_dict(), **stored,
                "evacuation": plan}

    def evacuate(self, node_id: str) -> dict:
        """Move every running workload off a draining node.

        A workload with no feasible destination is reported ``stranded`` and
        left assigned to the source; the caller decides whether to force-stop
        it. The node is marked offline only when the evacuation is clean.
        """
        node = self.store.require_node(node_id)
        plan = domain.evacuation_plan(
            self.store.list_nodes(), self.store.list_workloads(), node_id)
        applied: list[dict] = []
        for move in plan["moves"]:
            workload = self.store.require_workload(move["workload_id"])
            source = self.store.get_node(move["from"])
            target = self.store.get_node(move["to"])
            if source is None or target is None:
                continue
            source.release(workload)
            target.reserve(workload)
            target.last_seen = time.time()
            self.store.put_node(source)
            self.store.put_node(target)
            workload.assigned_node = target.node_id
            self.store.put_workload(workload)
            applied.append(move)
            self.store.append_event("workload.migrated", {
                "workload_id": workload.workload_id,
                "from": source.node_id, "to": target.node_id,
            })
        if plan["drained"]:
            node.status = domain.NodeStatus.OFFLINE
        else:
            node.status = domain.NodeStatus.DRAINING
        node.last_seen = time.time()
        self.store.put_node(node)
        self.store.append_event("node.evacuated", {
            "node_id": node_id, "moved": len(applied),
            "stranded": len(plan["stranded"]),
        })
        return {"ok": True, "node_id": node_id, "moves": applied,
                "stranded": plan["stranded"], "drained": plan["drained"],
                "node": node.to_dict()}

    def rebalance(self, threshold: float = 0.85, apply: bool = False) -> dict:
        """Plan (and optionally apply) moves away from overloaded nodes."""
        nodes = self.store.list_nodes()
        workloads = self.store.list_workloads()
        plan = domain.rebalance_plan(nodes, workloads, threshold=threshold)
        node_payloads = [node.to_dict() for node in nodes]
        green: dict[str, dict] = {}
        for item in workloads:
            if item.state is not WorkloadState.RUNNING:
                continue
            source = self.store.get_node(item.assigned_node) if item.assigned_node else None
            green[item.workload_id] = ecosystem.energy_plan(
                node_payloads, item.to_dict(),
                source=source.to_dict() if source else None)
        roaming = ecosystem.roaming_plan(
            [item.to_dict() for item in workloads
             if item.state is WorkloadState.RUNNING],
            node_payloads,
        )
        if not apply:
            return {"ok": True, "applied": 0, "green": green,
                    "roaming": roaming, **plan}
        by_id = {node.node_id: node for node in nodes}
        applied = 0
        for move in plan["moves"]:
            workload = self.store.require_workload(move["workload_id"])
            source = by_id.get(move["from"])
            target = by_id.get(move["to"])
            if source is None or target is None:
                continue
            source.release(workload)
            target.reserve(workload)
            self.store.put_node(source)
            self.store.put_node(target)
            workload.assigned_node = target.node_id
            self.store.put_workload(workload)
            applied += 1
        if applied:
            self.store.append_event("fleet.rebalanced", {"applied": applied,
                                                         "threshold": threshold})
        return {"ok": True, "applied": applied, **plan}

    # ------------------------------------------------------------------
    # observability
    # ------------------------------------------------------------------
    def predict(self, horizon_s: float = 3600.0) -> list[dict]:
        forecasts = domain.predict_fleet_faults(
            self.store.list_nodes(), horizon_s=horizon_s)
        return [forecast.to_dict() for forecast in forecasts]

    def energy(self, hours: float = 24.0) -> dict:
        return domain.energy_profile(self.store.list_nodes(), hours=hours)

    def health(self) -> dict:
        return domain.fleet_health(
            self.store.list_nodes(), self.store.list_workloads())

    def status(self) -> dict:
        nodes = self.store.list_nodes()
        workloads = self.store.list_workloads()
        node_payloads = [node.to_dict() for node in nodes]
        return {
            "ok": True,
            "health": domain.fleet_health(nodes, workloads),
            "metrics": self.store.metrics(),
            "energy": domain.energy_profile(nodes),
            "faults": [f.to_dict() for f in domain.predict_fleet_faults(nodes)[:5]],
            "sleep": ecosystem.sleep_plan(node_payloads),
            "roaming": ecosystem.roaming_plan(
                [workload.to_dict() for workload in workloads
                 if workload.state is WorkloadState.QUEUED],
                node_payloads,
            ),
        }

    def events(self, since: int = 0, limit: int = 200) -> list[dict]:
        return self.store.events_since(since, limit)

    def snapshot(self, label: str = "") -> dict:
        return self.store.snapshot(label)

    def restore(self, snapshot_id: str) -> dict:
        return self.store.restore(snapshot_id)

    def metrics(self) -> dict:
        return self.store.metrics()

    # ------------------------------------------------------------------
    # self-checks
    # ------------------------------------------------------------------
    def simulate(self) -> dict:
        """Replay the six states a fleet scheduler must survive.

        Runs against a temporary store so it never mutates live state. Each
        scenario is a real call through the same service methods a client uses,
        not a mocked branch.
        """
        scenarios: dict[str, dict] = {}
        with tempfile.TemporaryDirectory() as tmp:
            service = FleetService(Path(tmp) / "simulate.db")
            try:
                service.register_node({"node_id": "sim-a", "cpu_cores": 8,
                                       "memory_gb": 16, "capabilities": ["cpu"],
                                       "region": "local", "reliability": 0.99})
                service.register_node({"node_id": "sim-b", "cpu_cores": 4,
                                       "memory_gb": 8, "capabilities": ["cpu"],
                                       "region": "local", "reliability": 0.9})
                submitted = service.submit_workload({
                    "workload_id": "sim-w1", "cpu": 2, "memory_gb": 2,
                    "required_capabilities": ["cpu"], "priority": 80,
                })
                dispatched = service.dispatch("sim-w1")
                scenarios["success"] = {
                    "ok": submitted["created"] and dispatched["dispatched"] == 1,
                    "detail": dispatched["decisions"][0]["decision"]["chosen"],
                }
                try:
                    service.submit_workload({"workload_id": "sim-bad", "cpu": 0})
                    scenarios["malformed"] = {"ok": False, "detail": "accepted cpu=0"}
                except ValidationError as exc:
                    scenarios["malformed"] = {"ok": True, "detail": str(exc)}

                service.submit_workload({
                    "workload_id": "sim-w2", "cpu": 1, "memory_gb": 1,
                    "required_capabilities": ["cpu"], "priority": 30,
                })
                service.set_node_status("sim-a", "offline")
                service.set_node_status("sim-b", "offline")
                unplaceable = service.dispatch("sim-w2")
                scenarios["disconnection"] = {
                    "ok": unplaceable["dispatched"] == 0,
                    "bottlenecks": len(unplaceable["decisions"][0]["decision"]["bottlenecks"]),
                }
                service.set_node_status("sim-a", "online")
                service.set_node_status("sim-b", "online")

                service.submit_workload({
                    "workload_id": "sim-heavy", "cpu": 64, "memory_gb": 128,
                    "required_capabilities": ["cpu"],
                })
                overloaded = service.dispatch("sim-heavy")
                scenarios["overload"] = {
                    "ok": overloaded["dispatched"] == 0,
                    "detail": overloaded["decisions"][0]["decision"]["bottlenecks"][:1],
                }

                running = service.get_workload("sim-w1")
                source = running["assigned_node"]
                evacuated = service.evacuate(source)
                scenarios["provider_loss"] = {
                    "ok": evacuated["drained"] and len(evacuated["moves"]) >= 1,
                    "from": source,
                    "moved": len(evacuated["moves"]),
                }

                snap = service.snapshot("simulate")
                before = len(service.list_nodes())
                service.delete_node("sim-b")
                service.restore(snap["snapshot_id"])
                scenarios["restart_recovery"] = {
                    "ok": len(service.list_nodes()) == before,
                    "nodes": len(service.list_nodes()),
                }
            except Exception as exc:  # noqa: BLE001 - reported as a scenario failure
                scenarios["harness"] = {"ok": False, "detail": str(exc)}
        passed = sum(1 for result in scenarios.values() if result.get("ok"))
        return {"ok": passed == len(scenarios), "passed": passed,
                "total": len(scenarios), "scenarios": scenarios}

    def benchmark(self, iterations: int = 20) -> dict:
        """Measure the placement path against a deterministic synthetic fleet."""
        iterations = max(1, int(iterations))
        nodes = [
            Node(node_id=f"bench-{i}", cpu_cores=4 + (i % 4), memory_gb=8 + (i % 8),
                 capabilities=frozenset({"cpu", "gpu"} if i % 3 == 0 else {"cpu"}),
                 region="local", reliability=0.9 + (i % 10) / 100.0,
                 price_per_hour=(i % 5) * 0.01)
            for i in range(12)
        ]
        workload = Workload(workload_id="bench", cpu=2, memory_gb=2,
                            required_capabilities=frozenset({"cpu"}),
                            duration_s=60.0)
        samples: list[float] = []
        for _ in range(iterations):
            start = time.perf_counter()
            decision = domain.place_workload(nodes, workload)
            samples.append(time.perf_counter() - start)
            if not decision.placed:
                raise RuntimeError("benchmark fleet could not place the workload")
        samples.sort()
        p50 = samples[len(samples) // 2]
        p95 = samples[min(len(samples) - 1, int(len(samples) * 0.95))]
        return {
            "ok": True,
            "iterations": iterations,
            "nodes": len(nodes),
            "p50_ms": round(p50 * 1000.0, 6),
            "p95_ms": round(p95 * 1000.0, 6),
            "ops_per_sec": round(1.0 / max(p50, 1e-9), 2),
            "mean_ms": round(statistics.fmean(samples) * 1000.0, 6),
            "cost_model": "local CPU only",
            "network_transfer": "0 bytes",
        }

    def doctor(self) -> dict:
        report = ecosystem.probe()
        return {"ok": report["ok"], "ecosystem": report,
                "store": self.store.metrics()}
