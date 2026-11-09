"""Cross-subsystem wiring for mem20predictiverecallenginez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["causal_routing","context_compression","recall_events","focus_context","capability_routing","demand_forecast","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20causalroutingbrainz","mem20contextcompressionforgez","mem20eventstreamsuperhighwayz","mem20mixedinitiativefocusenginez","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def context_compression(text:str)->dict:
    try:
        from mem20contextcompressionforgez.domain import compress,compression_ratio
        c=compress(text or "recall context and history summary",0.5); return {"ok":True,"subsystem":"mem20contextcompressionforgez","ratio":compression_ratio(text or "recall context and history summary",c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20contextcompressionforgez","error":f"{type(exc).__name__}: {exc}"}
def recall_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("recall"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def focus_context(context:Mapping)->dict:
    try:
        from mem20mixedinitiativefocusenginez.domain import focus_score,suggest
        ctx=dict(context) or {"priority":1,"distractions":0}; return {"ok":True,"subsystem":"mem20mixedinitiativefocusenginez","focus_score":focus_score(ctx),"suggestions":len(suggest(ctx,[{"label":"recall","priority":1},{"label":"prefetch","priority":1}]))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20mixedinitiativefocusenginez","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["recall"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def demand_forecast(obs:Sequence[float])->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [1,2,2,3,4]): b.observe(v)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"causal_routing":causal_routing({"r":1},{"r":1}),"context_compression":context_compression("history"),"recall_events":recall_events("r",{}),"focus_context":focus_context({"priority":1}),"capability_routing":capability_routing("k",["r"]),"demand_forecast":demand_forecast([1,2,3])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
