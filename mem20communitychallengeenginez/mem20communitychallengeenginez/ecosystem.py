"""Cross-subsystem wiring for mem20communitychallengeenginez (6 peers, community-challenge specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["quest_rewards","challenge_events","loyalty_signal","engagement_signal","reward_routing","lifecycle_signal","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20dynamicquestrewardcomposerz","mem20eventstreamsuperhighwayz","mem20crossproductloyaltygraphz","mem20autonomoussaleslaboratoryz","mem20capabilitymarketplacez","mem20customerlifecycleenginez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def quest_rewards(goal:int,level:int=1)->dict:
    try:
        from mem20dynamicquestrewardcomposerz.domain import generate_quest,reward_for_quest,balance_quests,completion_rate
        q=generate_quest(difficulty=max(1,goal//10),seed=goal); r=reward_for_quest(q,player_level=level); bal=balance_quests([q,q]); cr=completion_rate(goal,max(1,goal+1))
        return {"ok":True,"subsystem":"mem20dynamicquestrewardcomposerz","reward":r,"balanced":len(bal) if isinstance(bal,list) else 0,"completion_rate":cr}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicquestrewardcomposerz","error":f"{type(exc).__name__}: {exc}"}

def challenge_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("challenges"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def loyalty_signal(user_products:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score,recommend_products
        g={}; add_edge(g,"community","challenges",1.0); add_edge(g,"community","rewards",0.8); ups=list(user_products) or ["community"]
        rec=recommend_products(g,ups,top=2); score=loyalty_score(ups,g)
        return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","recommendations":len(rec) if isinstance(rec,list) else 0,"loyalty_score":score}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}

def engagement_signal(participants:int)->dict:
    try:
        from mem20autonomoussaleslaboratoryz.domain import conversion_probability,pipeline_value,segment_leads
        leads=[{"deal_value":10,"budget":100,"authority":True,"need":True,"timeline_days":7,"touches":i%3} for i in range(max(1,participants))]
        val=pipeline_value(leads); seg=segment_leads(leads); conv=conversion_probability(leads[0],1)
        return {"ok":True,"subsystem":"mem20autonomoussaleslaboratoryz","engagement_value":val,"segments":{k:len(v) for k,v in seg.items()},"sample_conversion":conv}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomoussaleslaboratoryz","error":f"{type(exc).__name__}: {exc}"}

def reward_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["rewards"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def lifecycle_signal()->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,lifetime_value,retention_probability
        c={"tenure_months":3,"spend":50,"events":4}; return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"ltv":lifetime_value(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"quest_rewards":quest_rewards(10),"challenge_events":challenge_events("join",{"u":"a"}),"loyalty_signal":loyalty_signal(["community"]),"engagement_signal":engagement_signal(3),"reward_routing":reward_routing("pool",["rewards"]),"lifecycle_signal":lifecycle_signal()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
