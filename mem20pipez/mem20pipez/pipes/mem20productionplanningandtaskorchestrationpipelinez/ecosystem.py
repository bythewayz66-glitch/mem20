"""Cross-subsystem wiring for mem20pipez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["workcells","node_swarm","capacity_plan","task_containment","orchestration_events","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomousworkcellsz","mem20zerotouchnodeswarmz","mem20causalroutingbrainz","mem20faultcontainmentcellsz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def workcells(task:Mapping)->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell, enqueue, cell_health
        cell=create_cell("prod", capacity=4); enqueue(cell, dict(task) or {"id":"t1"}); h=cell_health(cell)
        return {"ok":True,"subsystem":"mem20autonomousworkcellsz","queued":h.get("queued"),"capacity":h.get("capacity")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def node_swarm()->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,quorum,register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":"a1","capacity":1,"availability":1.0,"capabilities":["task"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm)),"quorum":quorum(swarm)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def capacity_plan(load:Sequence[float])->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(load) or 5))
        for v in (load or [5,6,7,6,8]): b.observe(v)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def task_containment(task_id:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"task":task_id,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","task":task_id,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","task":task_id,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def orchestration_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("orchestration"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["orchestrate"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"workcells":workcells({"id":"t1"}),"node_swarm":node_swarm(),"capacity_plan":capacity_plan([5,6,7]),"task_containment":task_containment("t1"),"orchestration_events":orchestration_events("o",{}),"capability_routing":capability_routing("k",["o"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
