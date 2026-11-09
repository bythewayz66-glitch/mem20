"""Cross-subsystem wiring for mem20twinz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["lifecycle_context","quest_motivation","challenge_engagement","motivation_scenarios","motivation_events","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20customerlifecycleenginez","mem20dynamicquestrewardcomposerz","mem20communitychallengeenginez","mem20simz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def lifecycle_context()->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,retention_probability
        c={"days_since_signup":30,"purchases":2,"engagement":0.6,"recency_days":7}; return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}
def quest_motivation()->dict:
    try:
        from mem20dynamicquestrewardcomposerz.domain import generate_quest,reward_for_quest
        q=generate_quest(1,seed=3); r=reward_for_quest(q,1); return {"ok":True,"subsystem":"mem20dynamicquestrewardcomposerz","xp":r.get("xp")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicquestrewardcomposerz","error":f"{type(exc).__name__}: {exc}"}
def challenge_engagement()->dict:
    try:
        from mem20communitychallengeenginez.domain import challenge_report
        r=challenge_report("motivation",3,["p1"],30.0); return {"ok":True,"subsystem":"mem20communitychallengeenginez","report_ok":r.get("ok")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20communitychallengeenginez","error":f"{type(exc).__name__}: {exc}"}
def motivation_scenarios(motivation:float)->dict:
    try:
        from mem20simz.domain import counterfactual,outcome_probability
        orig={"state":{"motivation":motivation},"base_rate":0.5}; cf=counterfactual(orig,{"change":{"motivation":min(1.0,motivation+0.2)}}); prob=outcome_probability(orig,{"effect":0.1})
        return {"ok":True,"subsystem":"mem20simz","cf_motivation":cf.get("state",{}).get("motivation"),"outcome_probability":prob}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def motivation_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("motivation"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["motivate"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"lifecycle_context":lifecycle_context(),"quest_motivation":quest_motivation(),"challenge_engagement":challenge_engagement(),"motivation_scenarios":motivation_scenarios(0.5),"motivation_events":motivation_events("m",{}),"capability_routing":capability_routing("k",["m"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
