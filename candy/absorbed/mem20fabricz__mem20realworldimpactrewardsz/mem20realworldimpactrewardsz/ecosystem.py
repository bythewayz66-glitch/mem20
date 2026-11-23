"""Cross-subsystem wiring for mem20realworldimpactrewardsz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["quest_rewards","loyalty_impact","lifecycle_value","impact_events","reward_routing","impact_forecast","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20dynamicquestrewardcomposerz","mem20crossproductloyaltygraphz","mem20customerlifecycleenginez","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def quest_rewards(magnitude:float)->dict:
    try:
        from mem20dynamicquestrewardcomposerz.domain import generate_quest,reward_for_quest
        q=generate_quest(difficulty=max(1,int(round(magnitude))),seed=1); r=reward_for_quest(q, player_level=1)
        return {"ok":True,"subsystem":"mem20dynamicquestrewardcomposerz","quest_id":q.get("id"),"reward":r}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicquestrewardcomposerz","error":f"{type(exc).__name__}: {exc}"}
def loyalty_impact(user:str,score:float)->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score
        g={}; add_edge(g,user,"impact",max(0.0,float(score))); return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","loyalty_score":loyalty_score([user],g)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}
def lifecycle_value()->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,retention_probability
        c={"days_since_signup":30,"purchases":2,"engagement":0.7,"recency_days":3}; return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}
def impact_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("impact"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def reward_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["reward"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def impact_forecast(obs:Sequence[float])->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [1,2,2,3]): b.observe(v)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"quest_rewards":quest_rewards(1.0),"loyalty_impact":loyalty_impact("u",1.0),"lifecycle_value":lifecycle_value(),"impact_events":impact_events("i",{}),"reward_routing":reward_routing("k",["r"]),"impact_forecast":impact_forecast([1,2,3])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
