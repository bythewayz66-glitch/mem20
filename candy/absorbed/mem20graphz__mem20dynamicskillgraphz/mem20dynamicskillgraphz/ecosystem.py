"""Cross-subsystem wiring for mem20dynamicskillgraphz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["capability_match","quest_progression","lifecycle_progression","skill_events","causal_routing","context_compression","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20capabilitymarketplacez","mem20dynamicquestrewardcomposerz","mem20customerlifecycleenginez","mem20eventstreamsuperhighwayz","mem20causalroutingbrainz","mem20rewardforgez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def capability_match(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["skill"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def quest_progression()->dict:
    try:
        from mem20dynamicquestrewardcomposerz.domain import generate_quest,reward_for_quest
        q=generate_quest(1,seed=7); r=reward_for_quest(q,1); return {"ok":True,"subsystem":"mem20dynamicquestrewardcomposerz","xp":r.get("xp")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicquestrewardcomposerz","error":f"{type(exc).__name__}: {exc}"}
def lifecycle_progression()->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,retention_probability
        c={"days_since_signup":45,"purchases":4,"engagement":0.7,"recency_days":3}; return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}
def skill_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("skills"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause,causal_effect
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights)),"effect":causal_effect([1,1],[0,0])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def context_compression(text:str)->dict:
    try:
        from mem20rewardforgez.domain import compress,compression_ratio
        c=compress(text or "skill graph summary and learning path", 0.5); return {"ok":True,"subsystem":"mem20rewardforgez","ratio":compression_ratio(text or "skill graph summary and learning path", c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20rewardforgez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"capability_match":capability_match("k",["s"]),"quest_progression":quest_progression(),"lifecycle_progression":lifecycle_progression(),"skill_events":skill_events("e",{}),"causal_routing":causal_routing({"gap":1},{"gap":1}),"context_compression":context_compression("skill path")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
