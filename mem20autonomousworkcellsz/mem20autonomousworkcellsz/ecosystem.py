"""Cross-subsystem wiring for mem20autonomousworkcellsz (6 peers, workcell-specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["swarm_workers","capability_routing","work_events","cell_containment","focus_priority","capacity_forecast","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20zerotouchnodeswarmz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20mixedinitiativefocusenginez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p)
        sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def swarm_workers(task:Mapping, worker_count:int=2)->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import assign_task, discover, quorum, register_node
        swarm={"nodes":[]}
        for i in range(max(1,worker_count)):
            register_node(swarm,{"id":f"w{i+1}","capacity":1,"availability":1.0,"capabilities":["cpu"],"status":"ready","tasks":0})
        ready=discover(swarm); q=quorum(swarm); assigned=assign_task(swarm,dict(task))
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(ready) if isinstance(ready,list) else 0,"quorum":q,"assigned":assigned is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}

def capability_routing(key:str, capabilities:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); caps=list(capabilities) or ["cpu","io"]
        for c in caps: m.add(c)
        owner=m.locate(key); dist=m.distribution(keys=100)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":owner,"capabilities":len(caps),"distribution_keys":sum(dist.values()) if hasattr(dist,'values') else 100}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def work_events(name:str, payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("workcells"); publish(s,name,dict(payload)); tp=throughput(s)
        return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":tp}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def cell_containment(cell_name:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen, FaultContainmentCells
        cell=FaultContainmentCells()
        result=cell.call(lambda: {"cell":cell_name,"processed":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","cell":cell_name,"has_result":result is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","cell":cell_name,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}

def focus_priority(context:Mapping)->dict:
    try:
        from mem20mixedinitiativefocusenginez.domain import focus_health, focus_score, suggest, take_over
        ctx=dict(context)
        score=focus_score(ctx); health=focus_health(ctx); takeover=take_over(score, threshold=0.5)
        sugg=suggest(ctx,[{"id":"process"},{"id":"defer"},{"id":"escalate"}])
        return {"ok":True,"subsystem":"mem20mixedinitiativefocusenginez","score":float(score),"health":health,"take_over":bool(takeover),"suggestions":len(sugg) if isinstance(sugg,list) else 0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20mixedinitiativefocusenginez","error":f"{type(exc).__name__}: {exc}"}

def capacity_forecast(observations:Sequence[float], capacity:int=4)->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [2,3,3,4,3]): b.observe(v)
        fc=b.forecast(steps=1); headroom=b.capacity_for(capacity)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":fc.get("point"),"headroom":headroom}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"swarm_workers":swarm_workers({"id":"t1"}),"capability_routing":capability_routing("task-1",["cpu","io"]),"work_events":work_events("work.enqueued",{"task":"t1"}),"cell_containment":cell_containment("cell-a"),"focus_priority":focus_priority({"priority":1,"distractions":0}),"capacity_forecast":capacity_forecast([2,3,4,3])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
