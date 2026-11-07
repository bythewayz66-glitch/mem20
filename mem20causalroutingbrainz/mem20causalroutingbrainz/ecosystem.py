"""Cross-subsystem wiring for mem20causalroutingbrainz (6 peers, causal-routing specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["counterfactual_route","route_events","capability_target","failure_signal","health_signal","node_targets","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20counterfactualmemorysimulatorz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz","mem20universalhealthnervoussystemz","mem20zerotouchnodeswarmz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def counterfactual_route(base:Mapping, action:Mapping)->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import compare, counterfactual, outcome_probability
        orig={"state":dict(base),"base_rate":0.5}; cf=counterfactual(orig,{"change":dict(action)}); comp=compare(orig,cf); prob=outcome_probability(orig,{"effect":float(action.get("effect",0.1))})
        return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","diff_keys":len(comp) if isinstance(comp,dict) else 0,"outcome_probability":prob}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}

def route_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("causal-routing"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def capability_target(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["route"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs),"distribution_keys":sum(m.distribution(keys=100).values())}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def failure_signal(component:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen, FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"routed":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","component":component,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","component":component,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}

def health_signal(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all, overall, register_subsystem
        h={}
        for c in (components or ["svc"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}

def node_targets(task:Mapping)->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover, quorum, register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":"n1","capacity":1,"availability":1.0,"capabilities":["cpu"],"status":"ready"})
        ready=discover(swarm); return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(ready) if isinstance(ready,list) else 0,"quorum":quorum(swarm)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"counterfactual_route":counterfactual_route({"latency":1},{"effect":0.1}),"route_events":route_events("route",{"x":1}),"capability_target":capability_target("k",["r1"]),"failure_signal":failure_signal("r"),"health_signal":health_signal(["svc"]),"node_targets":node_targets({"id":"t"})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
