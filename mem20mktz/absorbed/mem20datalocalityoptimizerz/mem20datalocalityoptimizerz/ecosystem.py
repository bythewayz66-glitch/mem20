"""Cross-subsystem wiring for mem20datalocalityoptimizerz (6 peers)."""
from __future__ import annotations
import pathlib, sys
from typing import Mapping, Sequence
__all__=["node_topology","placement_events","placement_containment","node_health","placement_routing","capacity_forecast","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20zerotouchnodeswarmz","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20universalhealthnervoussystemz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def node_topology(nodes:Sequence[Mapping])->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,quorum,register_node
        swarm={"nodes":[]}
        for n in (list(nodes)[:3] or [{"id":"n1","capacity":1,"availability":1.0,"capabilities":["storage"],"status":"ready"}]):
            register_node(swarm,{"id":n.get("id","n"),"capacity":n.get("capacity_gb",1),"availability":1.0,"capabilities":["storage"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm)),"quorum":quorum(swarm)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def placement_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("locality"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def placement_containment(node_id:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen, FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"node":node_id,"safe":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","node":node_id,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","node":node_id,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def node_health(node_ids:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for nid in (list(node_ids) or ["n1"]): register_subsystem(h,nid,lambda _n=nid: {"ok":True,"node":_n})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def placement_routing(key:str,strategies:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); ss=list(strategies) or ["latency"]
        for s in ss: m.add(s)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"strategies":len(ss)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def capacity_forecast(usage:Sequence[float])->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(usage) or 5))
        for v in (usage or [20,25,22,28,30]): b.observe(v)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"node_topology":node_topology([{"id":"n1"}]),"placement_events":placement_events("p",{}),"placement_containment":placement_containment("n1"),"node_health":node_health(["n1"]),"placement_routing":placement_routing("k",["latency"]),"capacity_forecast":capacity_forecast([20,25])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
