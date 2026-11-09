"""Cross-subsystem wiring for mem20twinz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["execution_twin","business_twin","counterfactual_sim","twin_events","twin_routing","causal_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20twinz","mem20twinz","mem20simz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def execution_twin()->dict:
    try:
        from mem20twinz.domain import create_twin, drift
        t=create_twin({"id":"p"}); d=drift(t,{"id":"p","state":"ok"}); return {"ok":True,"subsystem":"mem20twinz","drift":d is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20twinz","error":f"{type(exc).__name__}: {exc}"}
def business_twin()->dict:
    try:
        from mem20twinz.domain import create_twin,twin_health
        t=create_twin("twinz"); h=twin_health(t); return {"ok":True,"subsystem":"mem20twinz","healthy":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20twinz","error":f"{type(exc).__name__}: {exc}"}
def counterfactual_sim()->dict:
    try:
        from mem20simz.domain import counterfactual,compare
        o={"x":1}; cf=counterfactual(o,{"change":{"x":2}}); return {"ok":True,"subsystem":"mem20simz","diff":len(compare(o,cf))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def twin_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("twinz"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def twin_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["twin"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"execution_twin":execution_twin(),"business_twin":business_twin(),"counterfactual_sim":counterfactual_sim(),"twin_events":twin_events("t",{}),"twin_routing":twin_routing("k",["t"]),"causal_routing":causal_routing({"x":1},{"x":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
