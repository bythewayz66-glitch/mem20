"""Cross-subsystem wiring for mem20contextcompressionforgez (6 peers, context-compression specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["stream_compressed","summary_quality","focus_retention","strategy_routing","budget_forecast","keep_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20eventstreamsuperhighwayz","mem20loreragcontentgeneratorz","mem20mixedinitiativefocusenginez","mem20capabilitymarketplacez","mem20demandforecastandcapacitybrainz","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def stream_compressed(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("compression"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def summary_quality(prompt:str)->dict:
    try:
        from mem20loreragcontentgeneratorz.domain import generate,quality_score,rank_adapters
        res=generate([{"text":"context to compress","source":"forge"}],prompt,adapter="summary"); q=quality_score(res.get("output",""),prompt); r=rank_adapters([{"name":"summary","score":0.8},{"name":"default","score":0.4}],prompt)
        return {"ok":True,"subsystem":"mem20loreragcontentgeneratorz","quality":float(q) if isinstance(q,(int,float)) else 0.0,"adapter":r[0]["name"] if r else "default"}
    except Exception as exc: return {"ok":False,"subsystem":"mem20loreragcontentgeneratorz","error":f"{type(exc).__name__}: {exc}"}
def focus_retention(context:Mapping)->dict:
    try:
        from mem20mixedinitiativefocusenginez.domain import focus_health,focus_score,suggest
        ctx=dict(context); score=focus_score(ctx); health=focus_health(ctx); s=suggest(ctx,[{"id":"keep"},{"id":"drop"}])
        return {"ok":True,"subsystem":"mem20mixedinitiativefocusenginez","score":float(score),"health":health,"suggestions":len(s) if isinstance(s,list) else 0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20mixedinitiativefocusenginez","error":f"{type(exc).__name__}: {exc}"}
def strategy_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["extractive"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"strategies":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def budget_forecast(observations:Sequence[float],budget:int=1000)->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [200,300,250,400,350]): b.observe(v)
        fc=b.forecast(steps=1); return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":fc.get("point"),"headroom":b.capacity_for(budget)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def keep_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","keep_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"stream_compressed":stream_compressed("c",{"r":0.5}),"summary_quality":summary_quality("summarize"),"focus_retention":focus_retention({"priority":1,"distractions":0}),"strategy_routing":strategy_routing("k",["extractive"]),"budget_forecast":budget_forecast([200,300]),"keep_routing":keep_routing({"relevance":1},{"relevance":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
