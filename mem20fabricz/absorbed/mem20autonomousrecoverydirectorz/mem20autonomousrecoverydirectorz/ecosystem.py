"""Cross-subsystem wiring for mem20autonomousrecoverydirectorz (6 peers, recovery-specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["fault_containment","healing_plan","health_signal","recovery_pipeline","incident_events","swarm_status","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20faultcontainmentcellsz","mem20selfhealingplansz","mem20universalhealthnervoussystemz","mem20pipez","mem20eventstreamsuperhighwayz","mem20zerotouchnodeswarmz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p)
        sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def fault_containment(component:str, fail_times:int=0) -> dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen, FaultContainmentCells
        cell=FaultContainmentCells()
        state={"n":0}
        def op():
            state["n"]+=1
            if state["n"]<=fail_times: raise RuntimeError("fault")
            return "ok"
        result=None; opened=False
        try:
            result=cell.call(component, op) if hasattr(cell,"call") else (cell.execute(component, op) if hasattr(cell,"execute") else op())
        except CircuitOpen:
            opened=True
        except Exception as e:
            result={"error": str(e)}
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","component":component,"opened":opened,"has_result": result is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}

def healing_plan(steps:Sequence[str]) -> dict:
    try:
        from mem20selfhealingplansz.domain import create_plan, plan_status
        plan=create_plan(list(steps) or ["diagnose","isolate","restore"])
        st=plan_status(plan)
        return {"ok":True,"subsystem":"mem20selfhealingplansz","steps":len(plan.get("steps",steps) if isinstance(plan,dict) else (steps or [])),"status":st}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}

def health_signal(components:Sequence[str]) -> dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all, overall, register_subsystem
        h={}
        for c in (components or ["api","db"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); ov=overall(h)
        return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":ov}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}

def recovery_pipeline(asset_id:str) -> dict:
    try:
        from mem20pipez.domain import recover, version_asset, vc_health
        versions=[version_asset(asset_id, "v1"), version_asset(asset_id, "v2")]
        rec=recover(versions, "v1")
        health=vc_health(versions)
        return {"ok":True,"subsystem":"mem20pipez","recovered":rec,"versions":len(versions),"health":health}
    except Exception as exc: return {"ok":False,"subsystem":"mem20pipez","error":f"{type(exc).__name__}: {exc}"}

def incident_events(incident:Mapping) -> dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("incidents"); publish(s,"incident.triaged",dict(incident)); tp=throughput(s)
        return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":tp}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def swarm_status(node_id:str="node-1") -> dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover, quorum, register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":node_id,"capacity":1,"availability":1.0,"capabilities":["cpu"],"status":"ready"})
        ready=discover(swarm); q=quorum(swarm)
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(ready) if isinstance(ready,list) else 0,"quorum":q}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"fault_containment":fault_containment("api",0),"healing_plan":healing_plan(["diagnose","restore"]),"health_signal":health_signal(["api","db"]),"recovery_pipeline":recovery_pipeline("asset-1"),"incident_events":incident_events({"severity":"high"}),"swarm_status":swarm_status("n1")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
