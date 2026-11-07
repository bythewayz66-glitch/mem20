"""Cross-subsystem wiring for mem20simz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["counterfactual_sim","business_twin","causal_routing","sim_events","sim_routing","sim_containment","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20counterfactualmemorysimulatorz","mem20realtimebusinesstwinz","mem20causalroutingbrainz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def counterfactual_sim(state:Mapping)->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import counterfactual,compare
        o={"state":dict(state)}; cf=counterfactual(o,{"change":{"x":state.get("x",0)+1}}); return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","diff_keys":len(compare(o,cf))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}
def business_twin()->dict:
    try:
        from mem20realtimebusinesstwinz.domain import create_twin,twin_health
        t=create_twin("simz"); h=twin_health(t); return {"ok":True,"subsystem":"mem20realtimebusinesstwinz","healthy":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20realtimebusinesstwinz","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def sim_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("simz"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def sim_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["sim"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def sim_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"counterfactual_sim":counterfactual_sim({"x":1}),"business_twin":business_twin(),"causal_routing":causal_routing({"s":1},{"s":1}),"sim_events":sim_events("s",{}),"sim_routing":sim_routing("k",["s"]),"sim_containment":sim_containment("s")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
