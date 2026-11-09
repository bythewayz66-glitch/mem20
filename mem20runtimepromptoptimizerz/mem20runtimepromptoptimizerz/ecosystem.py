"""Cross-subsystem wiring for mem20runtimepromptoptimizerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["context_compression","causal_routing","capability_routing","prompt_events","optimize_containment","cost_forecast","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20rewardforgez","mem20causalroutingbrainz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def context_compression(text:str)->dict:
    try:
        from mem20rewardforgez.domain import compress,compression_ratio
        c=compress(text or "prompt",0.5); return {"ok":True,"subsystem":"mem20rewardforgez","ratio":compression_ratio(text or "prompt",c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20rewardforgez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["optimize"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def prompt_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("prompts"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def optimize_containment(pid:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"prompt":pid,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","prompt":pid,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","prompt":pid,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def cost_forecast(obs:Sequence[float])->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [10,9,8]): b.observe(v)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"context_compression":context_compression("hello world prompt"),"causal_routing":causal_routing({"q":1},{"q":1}),"capability_routing":capability_routing("k",["o"]),"prompt_events":prompt_events("p",{}),"optimize_containment":optimize_containment("p1"),"cost_forecast":cost_forecast([10,9])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
