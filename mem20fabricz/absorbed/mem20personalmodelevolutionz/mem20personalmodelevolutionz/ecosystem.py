"""Cross-subsystem wiring for mem20personalmodelevolutionz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["collective_intel","skill_transfer","episodic_memory","evo_events","evo_routing","causal_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20collectivemodelintelligencez","mem20skillmemorytransferz","mem20episodicmemorygraphz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def collective_intel()->dict:
    try:
        from mem20collectivemodelintelligencez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20collectivemodelintelligencez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20collectivemodelintelligencez","error":f"{type(exc).__name__}: {exc}"}
def skill_transfer()->dict:
    try:
        from mem20skillmemorytransferz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20skillmemorytransferz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20skillmemorytransferz","error":f"{type(exc).__name__}: {exc}"}
def episodic_memory()->dict:
    try:
        from mem20episodicmemorygraphz.domain import create_episode,add_event
        ep=create_episode("evo"); add_event(ep,{"text":"adapt"}); return {"ok":True,"subsystem":"mem20episodicmemorygraphz","events":1}
    except Exception as exc: return {"ok":False,"subsystem":"mem20episodicmemorygraphz","error":f"{type(exc).__name__}: {exc}"}
def evo_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("modelevo"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def evo_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["evo"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"collective_intel":collective_intel(),"skill_transfer":skill_transfer(),"episodic_memory":episodic_memory(),"evo_events":evo_events("e",{}),"evo_routing":evo_routing("k",["e"]),"causal_routing":causal_routing({"x":1},{"x":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
