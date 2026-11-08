"""Cross-subsystem wiring for mem20outcomesimulationlabz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["counterfactual","business_twin","business_model","sim_events","sim_routing","causal_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20counterfactualmemorysimulatorz","mem20realtimebusinesstwinz","mem20businessmodelsimulatorz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def counterfactual()->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import counterfactual as cf,compare
        o={"x":1}; c=cf(o,{"change":{"x":2}}); return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","diff":len(compare(o,c))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}
def business_twin()->dict:
    try:
        from mem20realtimebusinesstwinz.domain import create_twin,twin_health
        t=create_twin("sim"); h=twin_health(t); return {"ok":True,"subsystem":"mem20realtimebusinesstwinz","healthy":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20realtimebusinesstwinz","error":f"{type(exc).__name__}: {exc}"}
def business_model()->dict:
    try:
        from mem20businessmodelsimulatorz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20businessmodelsimulatorz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20businessmodelsimulatorz","error":f"{type(exc).__name__}: {exc}"}
def sim_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("outsim"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def sim_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["sim"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"counterfactual":counterfactual(),"business_twin":business_twin(),"business_model":business_model(),"sim_events":sim_events("s",{}),"sim_routing":sim_routing("k",["s"]),"causal_routing":causal_routing({"x":1},{"x":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
