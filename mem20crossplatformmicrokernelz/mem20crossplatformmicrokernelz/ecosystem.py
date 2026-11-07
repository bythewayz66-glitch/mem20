"""Cross-subsystem wiring for mem20crossplatformmicrokernelz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["node_swarm","ipc_events","process_containment","kernel_health","capability_routing","memory_locality","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20zerotouchnodeswarmz","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20universalhealthnervoussystemz","mem20capabilitymarketplacez","mem20datalocalityoptimizerz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def node_swarm(proc:Mapping)->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,quorum,register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":"n1","capacity":1,"availability":1.0,"capabilities":["cpu"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm)),"quorum":quorum(swarm)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def ipc_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("microkernel"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def process_containment(pid:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen, FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"pid":pid,"isolated":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","pid":pid,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","pid":pid,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def kernel_health(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for c in (components or ["scheduler"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["ipc"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def memory_locality(pages:Sequence[int])->dict:
    try:
        from mem20datalocalityoptimizerz.domain import locality_report, optimal_placement, placement_score
        data={"id":"mem","size_gb":max(0.001,(len(pages) or 1)*0.001)}; nodes=[{"id":"n1","latency_ms":1,"cost_per_gb":0.01,"capacity_gb":10,"used_gb":0,"local":True},{"id":"n2","latency_ms":20,"cost_per_gb":0.02,"capacity_gb":10,"used_gb":0,"local":False}]
        place=optimal_placement(data,nodes); score=placement_score(nodes[0],data)
        rep=locality_report([{"local":True,"node":place.get("id") if isinstance(place,dict) else place}])
        return {"ok":True,"subsystem":"mem20datalocalityoptimizerz","placement":place.get("id") if isinstance(place,dict) else None,"score":score,"local_ratio":rep.get("ratio") if isinstance(rep,dict) else 0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20datalocalityoptimizerz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"node_swarm":node_swarm({"pid":"1"}),"ipc_events":ipc_events("ipc",{}),"process_containment":process_containment("1"),"kernel_health":kernel_health(["sched"]),"capability_routing":capability_routing("k",["ipc"]),"memory_locality":memory_locality([1,2])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
