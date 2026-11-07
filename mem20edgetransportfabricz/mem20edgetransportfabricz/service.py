"""Transport fabric service: real orchestration over domain/store/ecosystem.

Owns topology state, flow admission/routing/reservation, reroute/recovery,
health, events/snapshots, and cross-subsystem judgements. No stubs.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from . import domain, ecosystem
from .store import ConflictError, FabricStore, NotFoundError, StoreError


class ValidationError(ValueError):
    pass


def _idem(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


class TransportFabricService:
    def __init__(self, db_path: str | Path):
        self.store = FabricStore(db_path)

    # ---- topology ----
    def put_node(self, payload: Mapping[str, Any], expected_version: Optional[int] = None) -> Dict[str, Any]:
        node = domain.FabricNode(
            node_id=str(payload.get("node_id") or payload.get("id") or "").strip(),
            kind=str(payload.get("kind") or "edge"),
            region=str(payload.get("region") or ""),
            status=str(payload.get("status") or "online"),
            capacity_mbps=float(payload.get("capacity_mbps") or payload.get("bandwidth_mbps") or 1000.0),
            metadata=dict(payload.get("metadata") or {}),
        )
        node.validate()
        rec = self.store.put("node", node.node_id, node.__dict__, expected_version=expected_version)
        # peer: traffic admission baseline for node capacity + causal route baseline
        admission = ecosystem.traffic_admission(min(node.capacity_mbps, 100.0), rate_per_sec=max(1.0, node.capacity_mbps), capacity=max(1.0, node.capacity_mbps))
        causal = ecosystem.causal_route({"capacity": node.capacity_mbps, "status": 1.0 if node.status == "online" else 0.2}, {"capacity": 0.01, "status": 0.5})
        return {"ok": True, "node": rec["payload"], "version": rec["version"], "admission_signal": admission, "causal_signal": causal}

    def get_node(self, node_id: str) -> Dict[str, Any]:
        return self.store.require("node", node_id)["payload"]

    def list_nodes(self) -> List[Dict[str, Any]]:
        return [r["payload"] for r in self.store.list("node")]

    def put_link(self, payload: Mapping[str, Any], expected_version: Optional[int] = None) -> Dict[str, Any]:
        src = str(payload.get("src") or payload.get("from") or "").strip()
        dst = str(payload.get("dst") or payload.get("to") or "").strip()
        link = domain.FabricLink(
            link_id=str(payload.get("link_id") or payload.get("id") or f"{src}->{dst}"),
            src=src, dst=dst,
            bandwidth_mbps=float(payload.get("bandwidth_mbps") or 100.0),
            latency_ms=float(payload.get("latency_ms") or 10.0),
            loss_rate=float(payload.get("loss_rate") or 0.0),
            jitter_ms=float(payload.get("jitter_ms") or 0.0),
            status=str(payload.get("status") or "up"),
            cost=float(payload.get("cost") or 1.0),
            reserved_mbps=float(payload.get("reserved_mbps") or 0.0),
            tags=list(payload.get("tags") or []),
            metadata=dict(payload.get("metadata") or {}),
        )
        link.validate()
        rec = self.store.put("link", link.link_id, {
            **{k: v for k, v in link.__dict__.items()},
        }, expected_version=expected_version)
        containment = ecosystem.fault_containment(probe_ok=link.status != "down")
        admission = ecosystem.traffic_admission(min(link.available_mbps, 50.0), rate_per_sec=max(1.0, link.bandwidth_mbps), capacity=max(1.0, link.bandwidth_mbps))
        telemetry = ecosystem.telemetry_publish(link.link_id, "link.upserted", {"src": link.src, "dst": link.dst, "status": link.status, "bandwidth_mbps": link.bandwidth_mbps})
        return {"ok": True, "link": rec["payload"], "version": rec["version"], "containment_signal": containment, "admission_signal": admission, "telemetry": telemetry}

    def set_link_status(self, link_id: str, status: str) -> Dict[str, Any]:
        rec = self.store.require("link", link_id)
        payload = dict(rec["payload"])
        payload["status"] = str(status)
        if status == "down":
            payload["last_failure"] = time.time()
        saved = self.store.put("link", link_id, payload, expected_version=rec["version"])
        recovery = ecosystem.recovery_plan("high" if status == "down" else "low", component=f"link:{link_id}")
        containment = ecosystem.fault_containment(probe_ok=status != "down", threshold=1)
        telemetry = ecosystem.telemetry_publish(link_id, "link.status", {"status": status})
        return {"ok": True, "link": saved["payload"], "recovery_signal": recovery, "containment_signal": containment, "telemetry": telemetry}

    def list_links(self) -> List[Dict[str, Any]]:
        return [r["payload"] for r in self.store.list("link")]

    def delete_object(self, kind: str, ident: str) -> Dict[str, Any]:
        return {"ok": self.store.delete(kind, ident), "kind": kind, "id": ident}

    # ---- fabric model ----
    def _topology(self):
        nodes = {}
        for r in self.store.list("node", limit=5000):
            p = r["payload"]
            nodes[p["node_id"]] = domain.FabricNode(
                node_id=p["node_id"], kind=p.get("kind", "edge"), region=p.get("region", ""),
                status=p.get("status", "online"), capacity_mbps=float(p.get("capacity_mbps", 1000.0)),
                metadata=dict(p.get("metadata") or {}))
        links = {}
        for r in self.store.list("link", limit=5000):
            p = r["payload"]
            links[p["link_id"]] = domain.FabricLink(
                link_id=p["link_id"], src=p["src"], dst=p["dst"],
                bandwidth_mbps=float(p.get("bandwidth_mbps", 100.0)), latency_ms=float(p.get("latency_ms", 10.0)),
                loss_rate=float(p.get("loss_rate", 0.0)), jitter_ms=float(p.get("jitter_ms", 0.0)),
                status=str(p.get("status", "up")), cost=float(p.get("cost", 1.0)),
                reserved_mbps=float(p.get("reserved_mbps", 0.0)), tags=list(p.get("tags") or []),
                metadata=dict(p.get("metadata") or {}))
        # ensure nodes referenced by links exist
        for l in links.values():
            nodes.setdefault(l.src, domain.FabricNode(node_id=l.src))
            nodes.setdefault(l.dst, domain.FabricNode(node_id=l.dst))
        return nodes, links

    # ---- flows / routing ----
    def admit(self, payload: Mapping[str, Any], idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        if idempotency_key:
            prev = self.store.idem_get(idempotency_key)
            if prev:
                got = self.store.get("flow", prev)
                if got:
                    return {"ok": True, "idempotent": True, "flow": got["payload"]}
        flow = domain.FlowDemand(
            flow_id=str(payload.get("flow_id") or payload.get("id") or uuid.uuid4().hex[:12]),
            src=str(payload.get("src") or ""),
            dst=str(payload.get("dst") or ""),
            demand_mbps=float(payload.get("demand_mbps") or payload.get("demand") or 1.0),
            priority=int(payload.get("priority") or 1),
            qos=str(payload.get("qos") or "standard"),
            max_latency_ms=(float(payload["max_latency_ms"]) if payload.get("max_latency_ms") is not None else None),
            min_bandwidth_mbps=(float(payload["min_bandwidth_mbps"]) if payload.get("min_bandwidth_mbps") is not None else None),
            payload_bytes=int(payload.get("payload_bytes") or 0),
            intermittent_ok=bool(payload.get("intermittent_ok", True)),
            metadata=dict(payload.get("metadata") or {}),
        )
        flow.validate()
        nodes, links = self._topology()
        decision = domain.admit_flow(nodes, links, flow)
        # peer judgements (real calls)
        causal = ecosystem.causal_route(
            {"latency_ms": decision.latency_ms if decision.path else 9999, "loss": 0.0, "priority": flow.priority, "demand": flow.demand_mbps},
            {"latency_ms": -0.02, "loss": -3.0, "priority": 0.01, "demand": -0.001},
        )
        admission = ecosystem.traffic_admission(flow.demand_mbps, rate_per_sec=1000.0, capacity=max(1.0, decision.bottleneck_mbps * 10 or 100.0))
        containment = ecosystem.fault_containment(probe_ok=decision.admitted or decision.fallback_used)
        mesh = ecosystem.mesh_resilience_probe(operation=f"admit:{flow.flow_id}", should_fail=False)
        telemetry = ecosystem.telemetry_publish(flow.flow_id, "flow.admitted" if decision.admitted else "flow.degraded", decision.to_dict(), stream_name="transport-fabric")
        record = {
            **flow.__dict__,
            "state": domain.FlowState.ADMITTED.value if decision.admitted else (domain.FlowState.PENDING.value if decision.fallback_used else domain.FlowState.DROPPED.value),
            "decision": decision.to_dict(),
            "sla": domain.sla_report(decision, flow),
            "signals": {"causal": causal, "traffic": admission, "containment": containment, "mesh": mesh, "telemetry": telemetry},
            "updated": time.time(),
        }
        saved = self.store.put("flow", flow.flow_id, record)
        self.store.record_placement(flow.flow_id, decision.to_dict())
        if idempotency_key:
            self.store.idem_put(idempotency_key, flow.flow_id)
        return {"ok": True, "idempotent": False, "flow": saved["payload"], "decision": decision.to_dict(), "sla": record["sla"], "signals": record["signals"]}

    def route(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        # lightweight route query (legacy-friendly shape + fabric details)
        src = str(payload.get("src") or "")
        dst = str(payload.get("dst") or "")
        nodes, links = self._topology()
        # include legacy neighbor-map routing as baseline
        neighbor = {}
        for l in links.values():
            neighbor.setdefault(l.src, []).append(l.dst)
            neighbor.setdefault(l.dst, [])
        legacy = domain.route_path(src, dst, neighbor)
        flow = domain.FlowDemand(flow_id=str(payload.get("flow_id") or _idem(payload)[:12]), src=src, dst=dst,
                                 demand_mbps=float(payload.get("demand_mbps") or 1.0), priority=int(payload.get("priority") or 1),
                                 max_latency_ms=(float(payload["max_latency_ms"]) if payload.get("max_latency_ms") is not None else None),
                                 intermittent_ok=bool(payload.get("intermittent_ok", True)))
        decision = domain.admit_flow(nodes, links, flow)
        causal = ecosystem.causal_route({"latency_ms": decision.latency_ms if decision.path else 9999, "priority": flow.priority},
                                        {"latency_ms": -0.01, "priority": 0.005})
        return {"ok": True, "path": decision.path or legacy, "legacy_path": legacy, "decision": decision.to_dict(), "causal_signal": causal}

    def reserve(self, flow_id: str) -> Dict[str, Any]:
        rec = self.store.require("flow", flow_id)
        flow = rec["payload"]
        decision = flow.get("decision") or {}
        link_ids = decision.get("links") or []
        demand = float(flow.get("demand_mbps") or 0.0)
        nodes, links = self._topology()
        res = domain.reserve_path(links, link_ids, demand)
        admission = ecosystem.traffic_admission(demand)
        containment = ecosystem.fault_containment(probe_ok=res.get("ok", False), threshold=1)
        if res.get("ok"):
            # persist link updates
            for lid in link_ids:
                l = links.get(lid)
                if l:
                    lrec = self.store.require("link", lid)
                    p = dict(lrec["payload"]); p["reserved_mbps"] = round(l.reserved_mbps, 6)
                    self.store.put("link", lid, p, expected_version=lrec["version"])
            flow["state"] = domain.FlowState.ACTIVE.value
            flow["reserved"] = True
            self.store.put("flow", flow_id, flow, expected_version=rec["version"])
            telemetry = ecosystem.telemetry_publish(flow_id, "flow.reserved", {"links": link_ids, "demand_mbps": demand})
        else:
            telemetry = ecosystem.telemetry_publish(flow_id, "flow.reserve_failed", res)
        return {"ok": bool(res.get("ok")), "reservation": res, "admission_signal": admission, "containment_signal": containment, "telemetry": telemetry, "flow_id": flow_id}

    def release(self, flow_id: str) -> Dict[str, Any]:
        rec = self.store.require("flow", flow_id)
        flow = rec["payload"]
        link_ids = (flow.get("decision") or {}).get("links") or []
        demand = float(flow.get("demand_mbps") or 0.0)
        nodes, links = self._topology()
        res = domain.release_path(links, link_ids, demand)
        for lid in link_ids:
            l = links.get(lid)
            if l:
                try:
                    lrec = self.store.require("link", lid)
                    p = dict(lrec["payload"]); p["reserved_mbps"] = round(l.reserved_mbps, 6)
                    self.store.put("link", lid, p, expected_version=lrec["version"])
                except Exception:
                    pass
        flow["state"] = domain.FlowState.COMPLETED.value
        flow["reserved"] = False
        self.store.put("flow", flow_id, flow, expected_version=rec["version"])
        telemetry = ecosystem.telemetry_publish(flow_id, "flow.released", {"links": link_ids})
        return {"ok": True, "release": res, "telemetry": telemetry}

    def reroute(self, flow_id: str, avoid_links: Optional[Sequence[str]] = None, reason: str = "link-failure") -> Dict[str, Any]:
        rec = self.store.require("flow", flow_id)
        flow = rec["payload"]
        nodes, links = self._topology()
        demand = domain.FlowDemand(
            flow_id=flow_id, src=flow["src"], dst=flow["dst"],
            demand_mbps=float(flow.get("demand_mbps") or 1.0), priority=int(flow.get("priority") or 1),
            qos=str(flow.get("qos") or "standard"),
            max_latency_ms=flow.get("max_latency_ms"), min_bandwidth_mbps=flow.get("min_bandwidth_mbps"),
            intermittent_ok=bool(flow.get("intermittent_ok", True)),
        )
        plan = domain.reroute_plan(nodes, links, demand, avoid_links=avoid_links or [])
        recovery = ecosystem.recovery_plan("high", component=f"flow:{flow_id}")
        containment = ecosystem.fault_containment(probe_ok=plan["decision"]["admitted"])
        mesh = ecosystem.mesh_resilience_probe(operation=f"reroute:{flow_id}")
        if plan["decision"]["path"]:
            flow["decision"] = plan["decision"]
            flow["state"] = domain.FlowState.REROUTED.value
            flow["reroute_reason"] = reason
            self.store.put("flow", flow_id, flow, expected_version=rec["version"])
            self.store.record_placement(flow_id, plan["decision"])
        telemetry = ecosystem.telemetry_publish(flow_id, "flow.rerouted", {"reason": reason, "avoided": list(avoid_links or []), "decision": plan["decision"]})
        return {"ok": True, **plan, "recovery_signal": recovery, "containment_signal": containment, "mesh_signal": mesh, "telemetry": telemetry}

    def list_flows(self) -> List[Dict[str, Any]]:
        return [r["payload"] for r in self.store.list("flow")]

    def get_flow(self, flow_id: str) -> Dict[str, Any]:
        return self.store.require("flow", flow_id)["payload"]

    # ---- status/observability ----
    def status(self) -> Dict[str, Any]:
        nodes, links = self._topology()
        health = domain.fabric_health(nodes, links)
        # also expose legacy transport_health shape over current links
        legacy = domain.transport_health([{"status": l.status} for l in links.values()])
        telemetry = ecosystem.telemetry_publish("fabric", "status", {"fabric_health": health.get("fabric_health"), "links": health.get("links")})
        return {"ok": True, "health": health, "legacy_health": legacy, "metrics": self.store.metrics(), "telemetry": telemetry}

    def doctor(self) -> Dict[str, Any]:
        probe = ecosystem.probe()
        st = self.status()
        # plus local fabric checks
        nodes, links = self._topology()
        local = {"ok": True, "nodes": len(nodes), "links": len(links), "degraded_or_down": [l.link_id for l in links.values() if l.status in ("down", "degraded", "intermittent")]}
        return {"ok": probe.get("ok", False) and local["ok"], "probe": probe, "local": local, "fabric": st["health"]}

    def events(self, since: int = 0, limit: int = 200):
        return self.store.events(since, limit)

    def placements(self, flow_id: Optional[str] = None, limit: int = 100):
        return self.store.placements(flow_id, limit)

    def snapshot(self, label: str = ""):
        return self.store.snapshot(label)

    def restore(self, snapshot_id: str):
        return self.store.restore(snapshot_id)

    # ---- scenarios/bench ----
    def simulate(self) -> Dict[str, Any]:
        # isolated simulation store operations via direct domain+ecosystem on temp-like logic? Use current store in a safe scenario namespace.
        scenarios = {}
        nodes = {
            "a": domain.FabricNode("a"), "b": domain.FabricNode("b"), "c": domain.FabricNode("c"),
        }
        links = {
            "a->b": domain.FabricLink("a->b", "a", "b", bandwidth_mbps=100, latency_ms=5, status="up"),
            "b->c": domain.FabricLink("b->c", "b", "c", bandwidth_mbps=80, latency_ms=8, status="up"),
            "a->c": domain.FabricLink("a->c", "a", "c", bandwidth_mbps=20, latency_ms=30, status="degraded"),
        }
        d = domain.admit_flow(nodes, links, domain.FlowDemand("s1", "a", "c", demand_mbps=5, priority=2, max_latency_ms=50))
        scenarios["direct_or_short_path"] = {"ok": bool(d.path) and d.admitted, "path": d.path, "latency_ms": d.latency_ms}
        links["a->b"].status = "down"
        d2 = domain.admit_flow(nodes, links, domain.FlowDemand("s2", "a", "c", demand_mbps=5, priority=1, max_latency_ms=100))
        scenarios["reroute_around_failure"] = {"ok": bool(d2.path), "path": d2.path, "fallback_used": d2.fallback_used}
        links["a->b"].status = "up"; links["b->c"].status = "intermittent"
        d3 = domain.admit_flow(nodes, links, domain.FlowDemand("s3", "a", "c", demand_mbps=5, priority=1, max_latency_ms=5, intermittent_ok=True))
        scenarios["intermittent_poor_connectivity"] = {"ok": bool(d3.path) and ("intermittent" in " ".join(d3.reasons).lower() or not d3.admitted or d3.fallback_used), "reasons": d3.reasons}
        links["b->c"].status = "up"
        res = domain.reserve_path(links, d.links, 5.0)
        domain.release_path(links, d.links, 5.0)
        scenarios["reserve_release"] = {"ok": bool(res.get("ok"))}
        alloc = domain.allocate_bandwidth(100, [{"id": "x", "demand": 1}, {"id": "y", "demand": 3}])
        scenarios["bandwidth_allocation"] = {"ok": alloc[1]["allocated"] == 75.0, "allocation": alloc}
        # ecosystem
        probe = ecosystem.probe()
        scenarios["peer_probe"] = {"ok": probe["ok"], "count": probe["count"]}
        telemetry = ecosystem.telemetry_publish("sim", "simulate", {"scenarios": len(scenarios)})
        recovery = ecosystem.recovery_plan("medium")
        mesh = ecosystem.mesh_resilience_probe("sim")
        scenarios["recovery_signal"] = {"ok": recovery.get("ok")}
        scenarios["mesh_signal"] = {"ok": mesh.get("ok")}
        scenarios["telemetry_signal"] = {"ok": telemetry.get("ok")}
        passed = sum(1 for v in scenarios.values() if v.get("ok"))
        return {"ok": passed == len(scenarios), "passed": passed, "total": len(scenarios), "scenarios": scenarios}

    def benchmark(self, iterations: int = 20) -> Dict[str, Any]:
        iterations = max(1, min(int(iterations), 200))
        nodes = {f"n{i}": domain.FabricNode(f"n{i}") for i in range(12)}
        ids = list(nodes.keys())
        links = {}
        for i, a in enumerate(ids):
            b = ids[(i + 1) % len(ids)]
            links[f"{a}->{b}"] = domain.FabricLink(f"{a}->{b}", a, b, bandwidth_mbps=100, latency_ms=5 + i)
            links[f"{a}->{ids[(i+2)%len(ids)]}"] = domain.FabricLink(f"{a}->{ids[(i+2)%len(ids)]}", a, ids[(i+2)%len(ids)], bandwidth_mbps=50, latency_ms=12 + i)
        t0 = time.perf_counter()
        admitted = 0
        for i in range(iterations):
            f = domain.FlowDemand(f"b{i}", ids[i % len(ids)], ids[(i + 5) % len(ids)], demand_mbps=1.0, priority=1)
            d = domain.admit_flow(nodes, links, f)
            if d.admitted or d.path:
                admitted += 1
        dt = max(1e-9, time.perf_counter() - t0)
        # peer touch in benchmark path? keep benchmark lean; doctor/simulate cover peers.
        return {"ok": True, "iterations": iterations, "admitted_or_routed": admitted, "elapsed_s": round(dt, 6), "ops_per_sec": round(iterations / dt, 3), "nodes": len(nodes), "links": len(links)}
