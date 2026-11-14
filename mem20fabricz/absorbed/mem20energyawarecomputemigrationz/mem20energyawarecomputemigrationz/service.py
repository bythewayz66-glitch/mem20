"""Energy-aware migration service: topology, planning, execution signals, state."""

from __future__ import annotations
import time, uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
from . import domain, ecosystem
from .store import ConflictError, MigrationStore, NotFoundError

class ValidationError(ValueError): pass

class MigrationService:
    def __init__(self, db_path):
        self.store = MigrationStore(db_path)

    def put_node(self, payload: Mapping[str, Any], expected_version=None):
        node = domain.ComputeNode(
            node_id=str(payload.get("node_id") or payload.get("id") or "").strip(),
            power_watts=float(payload.get("power_watts", 100)), speed=float(payload.get("speed", 1.0)),
            energy_rate=float(payload.get("energy_rate", 0.12)), carbon_g_per_kwh=float(payload.get("carbon_g_per_kwh", 400)),
            battery_pct=(float(payload["battery_pct"]) if payload.get("battery_pct") is not None else None),
            thermal_c=(float(payload["thermal_c"]) if payload.get("thermal_c") is not None else None),
            thermal_limit_c=float(payload.get("thermal_limit_c", 85)), renewable_pct=float(payload.get("renewable_pct", 0.0)),
            available=bool(payload.get("available", True)), region=str(payload.get("region","")), capacity=float(payload.get("capacity",1.0)),
            metadata=dict(payload.get("metadata") or {}))
        node.validate()
        rec = self.store.put("node", node.node_id, node.to_legacy(), expected_version=expected_version)
        energy_sig = ecosystem.energy_foundation([node.to_legacy()], budget_watts=max(100.0, node.power_watts*2), threshold_watts=node.power_watts*1.5)
        battery_sig = ecosystem.battery_schedule(10, [0,1,2,3], power_budget_watts=max(50.0, node.power_watts*3))
        return {"ok": True, "node": rec["payload"], "version": rec["version"], "energy_signal": energy_sig, "battery_signal": battery_sig}

    def list_nodes(self): return [r["payload"] for r in self.store.list("node")]
    def get_node(self, node_id): return self.store.require("node", node_id)["payload"]

    def put_workload(self, payload: Mapping[str, Any], expected_version=None):
        wid = str(payload.get("workload_id") or payload.get("id") or "").strip()
        if not wid: raise ValidationError("workload_id required")
        rec = self.store.put("workload", wid, {
            "id": wid, "workload_id": wid, "size": float(payload.get("size",1)), "priority": int(payload.get("priority",1)),
            "current_node": payload.get("current_node"), "deadline_s": payload.get("deadline_s"), "metadata": dict(payload.get("metadata") or {}),
        }, expected_version=expected_version)
        return {"ok": True, "workload": rec["payload"], "version": rec["version"]}

    def list_workloads(self): return [r["payload"] for r in self.store.list("workload")]
    def get_workload(self, wid): return self.store.require("workload", wid)["payload"]

    def _nodes(self): return [domain.ComputeNode(node_id=p["id"], power_watts=float(p.get("power_watts",100)), speed=float(p.get("speed",1)), energy_rate=float(p.get("energy_rate",0.12)), carbon_g_per_kwh=float(p.get("carbon_g_per_kwh",400)), battery_pct=p.get("battery_pct"), thermal_c=p.get("thermal_c"), thermal_limit_c=float(p.get("thermal_limit_c",85)), renewable_pct=float(p.get("renewable_pct",0)), available=bool(p.get("available",True)), region=str(p.get("region","")), capacity=float(p.get("capacity",1))) for p in self.list_nodes()]
    def _workloads(self): return [domain.Workload(workload_id=p["id"], size=float(p.get("size",1)), priority=int(p.get("priority",1)), current_node=p.get("current_node"), deadline_s=p.get("deadline_s")) for p in self.list_workloads()]

    def plan(self, payload: Mapping[str, Any] = None):
        payload = payload or {}
        nodes = [domain.ComputeNode(**{k:v for k,v in dict(n).items() if k in domain.ComputeNode.__dataclass_fields__}) if isinstance(n, dict) and "node_id" in n else domain.ComputeNode(node_id=n.get("id","n"), power_watts=float(n.get("power_watts",100)), speed=float(n.get("speed",1)), energy_rate=float(n.get("energy_rate",0.12)), carbon_g_per_kwh=float(n.get("carbon_g_per_kwh",400)), renewable_pct=float(n.get("renewable_pct",0)), available=bool(n.get("available",True)), thermal_c=n.get("thermal_c"), thermal_limit_c=float(n.get("thermal_limit_c",85)), battery_pct=n.get("battery_pct")) for n in (payload.get("nodes") or [r["payload"] for r in self.store.list("node")])] if payload.get("nodes") or self.list_nodes() else []
        workloads = [domain.Workload(workload_id=w.get("id") or w.get("workload_id","w"), size=float(w.get("size",1)), priority=int(w.get("priority",1)), current_node=w.get("current_node")) for w in (payload.get("workloads") or [r["payload"] for r in self.store.list("workload")])] if payload.get("workloads") or self.list_workloads() else []
        plan = domain.plan_migrations(nodes, workloads)
        # peer signals
        forecast = ecosystem.capacity_forecast([max(1.0, w.size) for w in workloads] or [1,1,2,1])
        goals = [{"id": m["workload_id"], "value": max(0.1, (m.get("decision") or {}).get("savings", 0.1))*100, "cost": 1} for m in plan["migrations"]] or [{"id":"none","value":1,"cost":1}]
        goal_sig = ecosystem.goal_priority(goals, budget=max(1.0, len(goals)))
        node_legs = [n.to_legacy() for n in nodes]
        locality = ecosystem.data_locality({"id":"wl","size_gb": (workloads[0].size/1000.0 if workloads else 1)}, [{"id":n.node_id,"capacity_gb":100,"used_gb":0,"latency_ms":5,"cost_per_gb":0.01} for n in nodes] or [{"id":"local","capacity_gb":100,"used_gb":0,"latency_ms":5,"cost_per_gb":0.01}])
        fabric = ecosystem.batch_fabric([{"id":w.workload_id,"region":(node_legs[0].get("region") if node_legs else "local") or "local","priority":w.priority,"status":"queued"} for w in workloads] or None)
        for m in plan["migrations"]: self.store.record_migration(m["workload_id"], m)
        return {"ok": True, "plan": plan, "signals": {"capacity_forecast": forecast, "goal_scheduler": goal_sig, "data_locality": locality, "batch_fabric": fabric}}

    def migrate(self, workload_id: str, target_node: str = None):
        w = self.get_workload(workload_id)
        nodes = self.list_nodes()
        if not nodes: raise ValidationError("no nodes registered")
        src = next((n for n in nodes if n.get("id")==w.get("current_node")), nodes[0])
        dst = next((n for n in nodes if n.get("id")==target_node), domain.greenest_node(nodes, w) or nodes[0])
        dec = domain.migrate_decision(src, dst, w)
        # apply
        prev = self.store.require("workload", workload_id)
        wp = dict(prev["payload"]); wp["current_node"] = dst.get("id"); wp["last_migration"] = {"from": src.get("id"), "to": dst.get("id"), "decision": dec, "ts": time.time()}
        self.store.put("workload", workload_id, wp, expected_version=prev["version"])
        self.store.record_migration(workload_id, {"from": src.get("id"), "to": dst.get("id"), "decision": dec})
        energy_sig = ecosystem.energy_foundation([src,dst])
        locality = ecosystem.data_locality({"id":workload_id,"size_gb":float(w.get("size",1))/1000.0,"node":src.get("id")}, [{"id":dst.get("id"),"capacity_gb":100,"used_gb":0,"latency_ms":5,"cost_per_gb":0.01}], src={"egress_cost":0.09}, dst={"egress_cost":0.0})
        return {"ok": True, "workload": wp, "decision": dec, "from": src.get("id"), "to": dst.get("id"), "energy_signal": energy_sig, "data_locality_signal": locality}

    def status(self):
        nodes = self._nodes(); workloads = self._workloads()
        summary = domain.fleet_energy_summary(nodes, workloads) if (nodes or workloads) else {"nodes":0,"workloads":0,"planned_migrations":0,"plan":{"placements":[],"migrations":[],"counts":{}}}
        energy = ecosystem.energy_foundation([n.to_legacy() for n in nodes] or [{"id":"idle","power_watts":0}])
        forecast = ecosystem.capacity_forecast([w.size for w in workloads] or [0])
        return {"ok": True, "summary": summary, "metrics": self.store.metrics(), "energy_signal": energy, "capacity_signal": forecast}

    def doctor(self):
        probe = ecosystem.probe()
        st = self.status()
        return {"ok": probe.get("ok") and st.get("ok"), "probe": probe, "status": {"nodes": st["summary"]["nodes"], "workloads": st["summary"]["workloads"]}}

    def events(self, since=0, limit=200): return self.store.events(since, limit)
    def migrations(self, limit=100): return self.store.migrations(limit)
    def snapshot(self, label=""): return self.store.snapshot(label)
    def restore(self, snapshot_id): return self.store.restore(snapshot_id)

    def simulate(self):
        scenarios = {}
        nodes = [{"id":"dirty","power_watts":200,"speed":1,"energy_rate":0.2,"carbon_g_per_kwh":600,"renewable_pct":0},
                 {"id":"green","power_watts":50,"speed":2,"energy_rate":0.1,"carbon_g_per_kwh":100,"renewable_pct":80}]
        w = {"id":"w1","size":10}
        scenarios["greenest_selection"] = {"ok": domain.greenest_node(nodes,w)["id"]=="green"}
        dec = domain.migrate_decision(nodes[0], nodes[1], w)
        scenarios["migration_decision"] = {"ok": dec["migrate"] and dec["savings"]>0, "decision": dec}
        plan = domain.migration_plan([w], nodes)
        scenarios["migration_plan"] = {"ok": plan[0]["target"]=="green", "plan": plan}
        cn = [domain.ComputeNode(node_id=n["id"], **{k:v for k,v in n.items() if k!="id"}) for n in nodes]
        cw = [domain.Workload(workload_id="w1", size=10, current_node="dirty")]
        adv = domain.plan_migrations(cn, cw)
        scenarios["advanced_plan"] = {"ok": len(adv["migrations"])>=1}
        probe = ecosystem.probe()
        scenarios["peer_probe"] = {"ok": probe["ok"], "count": probe["count"]}
        energy = ecosystem.energy_foundation(nodes)
        battery = ecosystem.battery_schedule(10,[0,1],500,{0:50,1:40})
        forecast = ecosystem.capacity_forecast([10,12,9])
        scenarios["energy_signal"] = {"ok": energy["ok"]}
        scenarios["battery_signal"] = {"ok": battery["ok"]}
        scenarios["capacity_signal"] = {"ok": forecast["ok"]}
        passed = sum(1 for v in scenarios.values() if v.get("ok"))
        return {"ok": passed==len(scenarios), "passed": passed, "total": len(scenarios), "scenarios": scenarios}

    def benchmark(self, iterations=20):
        import time as _t
        nodes=[{"id":f"n{i}","power_watts":50+i*10,"speed":1+i*0.1,"energy_rate":0.1,"carbon_g_per_kwh":200+i*10} for i in range(8)]
        w={"id":"w","size":10}; t0=_t.perf_counter()
        for _ in range(max(1,int(iterations))): domain.greenest_node(nodes,w); domain.migration_plan([w],nodes)
        dt=max(1e-9,_t.perf_counter()-t0)
        return {"ok": True, "iterations": int(iterations), "elapsed_s": round(dt,6), "ops_per_sec": round(int(iterations)/dt,3)}
