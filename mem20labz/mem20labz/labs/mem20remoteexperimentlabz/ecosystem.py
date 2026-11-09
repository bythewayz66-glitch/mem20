"""Cross-subsystem wiring for mem20labz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["workcell_execution","node_swarm","experiment_events","run_containment","scenario_compare","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomousworkcellsz","mem20zerotouchnodeswarmz","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20simz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def workcell_execution(exp:Mapping)->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,enqueue,cell_health
        cell=create_cell("exp",capacity=2); enqueue(cell,{"id":exp.get("id","e1"),"type":"experiment"}); h=cell_health(cell)
        return {"ok":True,"subsystem":"mem20autonomousworkcellsz","queued":h.get("queued")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def node_swarm()->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":"lab1","capacity":1,"availability":1.0,"capabilities":["run"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def experiment_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("experiments"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def run_containment(exp_id:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"exp":exp_id,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","exp":exp_id,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","exp":exp_id,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def scenario_compare(a:Mapping,b:Mapping)->dict:
    try:
        from mem20simz.domain import compare
        return {"ok":True,"subsystem":"mem20simz","diff_keys":len(compare(dict(a),dict(b)))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["experiment"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"workcell_execution":workcell_execution({"id":"e1"}),"node_swarm":node_swarm(),"experiment_events":experiment_events("e",{}),"run_containment":run_containment("e1"),"scenario_compare":scenario_compare({"score":1},{"score":2}),"capability_routing":capability_routing("k",["e"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
