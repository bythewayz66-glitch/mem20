"""Cross-subsystem wiring for mem20collectivemodelintelligencez (6 peers, collective-model specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["model_fusion","generation_quality","model_routing","ensemble_events","model_health","causal_route","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20livemodelfusionz","mem20loreragcontentgeneratorz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20universalhealthnervoussystemz","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def model_fusion(models:Sequence[Mapping])->dict:
    try:
        from mem20livemodelfusionz.domain import ensemble_vote, fuse, select_best, weight_by_confidence
        ms=list(models) or [{"id":"a","accuracy":0.8,"confidence":0.9},{"id":"b","accuracy":0.7,"confidence":0.8}]
        fused=fuse(ms); best=select_best(ms,"accuracy"); w=weight_by_confidence(ms); vote=ensemble_vote([m.get("prediction","yes") for m in ms] or ["yes","no","yes"])
        return {"ok":True,"subsystem":"mem20livemodelfusionz","fused":fused,"best":best.get("id") if isinstance(best,dict) else best,"weighted":len(w) if isinstance(w,list) else 0,"vote":vote}
    except Exception as exc: return {"ok":False,"subsystem":"mem20livemodelfusionz","error":f"{type(exc).__name__}: {exc}"}

def generation_quality(prompt:str)->dict:
    try:
        from mem20loreragcontentgeneratorz.domain import generate,quality_score,rank_adapters
        res=generate([{"text":"model context","source":"cmi"}],prompt,adapter="model"); q=quality_score(res.get("output",""),prompt); r=rank_adapters([{"name":"model","score":0.8},{"name":"default","score":0.4}],prompt)
        return {"ok":True,"subsystem":"mem20loreragcontentgeneratorz","quality":float(q) if isinstance(q,(int,float)) else 0.0,"adapter":r[0]["name"] if r else "default","output_len":len(str(res.get("output","")))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20loreragcontentgeneratorz","error":f"{type(exc).__name__}: {exc}"}

def model_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["inference"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def ensemble_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("collective-model"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def model_health(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all, overall, register_subsystem
        h={}
        for c in (components or ["model-a"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}

def causal_route(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause, routing_report
        score=route_by_cause(dict(features),dict(weights)); rep=routing_report()
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":score,"report_ok":rep.get("ok")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"model_fusion":model_fusion([]),"generation_quality":generation_quality("ensemble"),"model_routing":model_routing("m1",["inference"]),"ensemble_events":ensemble_events("e",{"x":1}),"model_health":model_health(["a"]),"causal_route":causal_route({"latency":0.1},{"latency":-1.0})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
