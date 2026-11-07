"""Cross-subsystem wiring for mem20roamingworkloadschedulerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["node_swarm","workcell_queue","capacity_forecast","schedule_events","migration_containment","scheduler_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20zerotouchnodeswarmz","mem20autonomousworkcellsz","mem20demandforecastandcapacitybrainz","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def node_swarm()->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":"n1","capacity":2,"availability":1.0,"capabilities":["work"],"status":"ready"})
        register_node(swarm,{"id":"n2","capacity":2,"availability":1.0,"capabilities":["work"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def workcell_queue(task:Mapping)->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,enqueue,cell_health
        c=create_cell("sched",4); enqueue(c,dict(task)); h=cell_health(c); return {"ok":True,"subsystem":"mem20autonomousworkcellsz","queued":h.get("queued")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def capacity_forecast(loads:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(loads) or 5))
        for v in (loads or [1,2,2]): b.observe(v)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def schedule_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("scheduler"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def migration_containment(wid:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"workload":wid,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","workload":wid,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","workload":wid,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def scheduler_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["schedule"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"node_swarm":node_swarm(),"workcell_queue":workcell_queue({"id":"w1"}),"capacity_forecast":capacity_forecast([1,2]),"schedule_events":schedule_events("s",{}),"migration_containment":migration_containment("w1"),"scheduler_routing":scheduler_routing("k",["s"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
