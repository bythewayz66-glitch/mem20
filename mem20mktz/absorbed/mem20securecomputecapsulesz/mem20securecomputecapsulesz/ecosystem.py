"""Cross-subsystem wiring for mem20securecomputecapsulesz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["capsule_containment","recovery_plans","workload_identity","capsule_routing","capsule_events","capsule_config","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20faultcontainmentcellsz","mem20selfhealingplansz","mem20secretslessworkloadidentityz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20deterministicconfigurationgraphz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def capsule_containment(cid:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"capsule":cid,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","capsule":cid,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","capsule":cid,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def recovery_plans(steps:Sequence[str])->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,plan_status
        p=create_plan(list(steps) or ["restart"]); return {"ok":True,"subsystem":"mem20selfhealingplansz","status":plan_status(p),"steps":len(list(steps) or ["restart"])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def workload_identity(workload:str)->dict:
    try:
        from mem20secretslessworkloadidentityz.domain import issue_identity,verify
        i=issue_identity(workload); return {"ok":True,"subsystem":"mem20secretslessworkloadidentityz","valid":verify(i).get("valid")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20secretslessworkloadidentityz","error":f"{type(exc).__name__}: {exc}"}
def capsule_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["run"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def capsule_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("capsules"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def capsule_config(cfg:Mapping)->dict:
    try:
        from mem20deterministicconfigurationgraphz.domain import add_node,validate
        g={}; add_node(g,"capsule",dict(cfg)); v=validate(g); return {"ok":True,"subsystem":"mem20deterministicconfigurationgraphz","valid":v.get("valid")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20deterministicconfigurationgraphz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"capsule_containment":capsule_containment("c1"),"recovery_plans":recovery_plans(["r"]),"workload_identity":workload_identity("cap"),"capsule_routing":capsule_routing("k",["r"]),"capsule_events":capsule_events("c",{}),"capsule_config":capsule_config({"cpu":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
