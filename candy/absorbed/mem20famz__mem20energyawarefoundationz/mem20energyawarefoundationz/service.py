from __future__ import annotations
from typing import Any, Dict, Mapping, Sequence
from . import domain, ecosystem
from .store import FoundationStore
class ValidationError(ValueError): pass
class FoundationService:
    def __init__(self, db_path): self.store=FoundationStore(db_path)
    def put_device(self, payload: Mapping[str,Any], expected_version=None):
        did=str(payload.get("device_id") or payload.get("id") or "").strip()
        if not did: raise ValidationError("device_id required")
        rec=self.store.put("device", did, {"id":did,"device_id":did,"power_watts":float(payload.get("power_watts",0)),"max_watts":float(payload.get("max_watts",0)),"priority":int(payload.get("priority",1)),"tags":list(payload.get("tags") or [])})
        tel=ecosystem.telemetry_aggregate([{"player":did,"action":"register","watts":payload.get("power_watts",0)}])
        return {"ok":True,"device":rec["payload"],"version":rec["version"],"telemetry_signal":tel}
    def list_devices(self): return [r["payload"] for r in self.store.list("device")]
    def put_policy(self, payload: Mapping[str,Any]):
        pid=str(payload.get("policy_id") or payload.get("id") or "default")
        rec=self.store.put("policy", pid, {"id":pid,"policy_id":pid,"budget_watts":float(payload.get("budget_watts",0)),"default_threshold_watts":float(payload.get("default_threshold_watts",0)),"device_thresholds":dict(payload.get("device_thresholds") or {}),"target_reduction":float(payload.get("target_reduction",0.1))})
        return {"ok":True,"policy":rec["payload"],"version":rec["version"]}
    def evaluate(self, policy_id="default", devices=None):
        devs=[dict(d) for d in (devices or self.list_devices())]
        pol=self.store.get("policy",policy_id); policy=(pol["payload"] if pol else {"budget_watts":sum(d.get("max_watts",0) or d.get("power_watts",0)*1.5 for d in devs),"default_threshold_watts":0,"target_reduction":0.1})
        result=domain.evaluate(devs, policy)
        resources={"power_watts": float(policy.get("budget_watts") or sum(d.get("power_watts",0) for d in devs) or 1)}
        usage={"power_watts": float(result["budget"]["total_watts"])}
        gov=ecosystem.resource_governance(resources, usage)
        twin=ecosystem.business_twin_alerts({"total_watts":usage["power_watts"], "devices":len(devs)}, {"total_watts": resources["power_watts"]*0.9})
        fabric=ecosystem.ambient_fabric([{"cpu":1,"memory":1,"storage":1,"status":"online","id":d.get("id")} for d in devs] or [{"cpu":1,"memory":1,"storage":1,"status":"online"}])
        orch=ecosystem.orchestrate_actions(result.get("actions") or [])
        cell=ecosystem.action_workcell(result.get("actions") or [{"device":"none","action":"noop"}])
        return {"ok":result.get("ok",True),"result":result,"signals":{"resource_governor":gov,"business_twin":twin,"ambient_fabric":fabric,"orchestration":orch,"workcell":cell}}
    def status(self):
        devs=self.list_devices(); ev=self.evaluate() if devs else {"ok":True,"result":{"daily_kwh":0,"budget":{"total_watts":0}},"signals":{}}
        tel=ecosystem.telemetry_aggregate([{"player":d.get("id"),"action":"status","watts":d.get("power_watts",0)} for d in devs] or [{"player":"idle","action":"status"}])
        return {"ok":True,"devices":len(devs),"metrics":self.store.metrics(),"evaluation":ev,"telemetry_signal":tel}
    def doctor(self): p=ecosystem.probe(); return {"ok":p.get("ok"),"probe":p,"metrics":self.store.metrics()}
    def events(self,since=0,limit=200): return self.store.events(since,limit)
    def snapshot(self,label=""): return self.store.snapshot(label)
    def restore(self,sid): return self.store.restore(sid)
    def simulate(self):
        devs=[{"id":"a","power_watts":120},{"id":"b","power_watts":80}]
        pol={"budget_watts":150,"default_threshold_watts":100,"target_reduction":0.2}
        res=domain.evaluate(devs,pol)
        probe=ecosystem.probe()
        ok = res["budget"]["within_budget"]==False and any(c["exceeded"] for c in res["threshold_checks"]) and probe["ok"]
        return {"ok": ok, "passed": 3 if ok else 0, "total": 3, "scenarios": {"budget_exceeded": {"ok": not res["budget"]["within_budget"]}, "threshold_exceeded": {"ok": any(c["exceeded"] for c in res["threshold_checks"])}, "peer_probe": {"ok": probe["ok"], "count": probe["count"]}}, "result": res}
    def benchmark(self, iterations=20):
        import time as _t; devs=[{"id":"a","power_watts":100}]; pol={"budget_watts":500}
        t0=_t.perf_counter();
        for _ in range(max(1,int(iterations))): domain.evaluate(devs,pol)
        dt=max(1e-9,_t.perf_counter()-t0); return {"ok":True,"iterations":int(iterations),"ops_per_sec":round(int(iterations)/dt,3)}
