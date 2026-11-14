"""Cross-subsystem wiring for mem20deterministicconfigurationgraphz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["config_events","rollout_containment","healing_plans","config_health","node_distribution","config_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20selfhealingplansz","mem20universalhealthnervoussystemz","mem20zerotouchnodeswarmz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def config_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("config"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def rollout_containment(node_id:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"node":node_id,"config_ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","node":node_id,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","node":node_id,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def healing_plans(steps:Sequence[str])->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,plan_status
        p=create_plan(list(steps) or ["rollback"]); return {"ok":True,"subsystem":"mem20selfhealingplansz","status":plan_status(p),"steps":len(list(steps) or ["rollback"])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def config_health(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for c in (list(components) or ["config"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def node_distribution(node_ids:Sequence[str])->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,quorum,register_node
        swarm={"nodes":[]}
        for nid in (list(node_ids)[:3] or ["n1"]): register_node(swarm,{"id":nid,"capacity":1,"availability":1.0,"capabilities":["config"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm)),"quorum":quorum(swarm)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def config_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["resolve"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"config_events":config_events("c",{}),"rollout_containment":rollout_containment("n1"),"healing_plans":healing_plans(["rollback"]),"config_health":config_health(["cfg"]),"node_distribution":node_distribution(["n1"]),"config_routing":config_routing("k",["resolve"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
