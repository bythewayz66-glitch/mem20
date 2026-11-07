"""Cross-subsystem wiring for mem20rewardforgez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["quest_reward_shapes","impact_rewards","counterfactual_shaping","reward_events","reward_routing","causal_weighting","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20dynamicquestrewardcomposerz","mem20realworldimpactrewardsz","mem20counterfactualmemorysimulatorz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def quest_reward_shapes()->dict:
    try:
        from mem20dynamicquestrewardcomposerz.domain import generate_quest,reward_for_quest
        q=generate_quest(difficulty=2,seed=2); r=reward_for_quest(q,1); return {"ok":True,"subsystem":"mem20dynamicquestrewardcomposerz","reward":r}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicquestrewardcomposerz","error":f"{type(exc).__name__}: {exc}"}
def impact_rewards()->dict:
    try:
        from mem20realworldimpactrewardsz.domain import record_impact,compute_reward
        i={}; record_impact(i,"u","act",2.0); return {"ok":True,"subsystem":"mem20realworldimpactrewardsz","reward":compute_reward(i,"u")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20realworldimpactrewardsz","error":f"{type(exc).__name__}: {exc}"}
def counterfactual_shaping(state:Mapping)->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import counterfactual,compare
        o={"state":dict(state)}; cf=counterfactual(o,{"change":{"bonus":1}}); return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","diff_keys":len(compare(o,cf))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}
def reward_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("rewards"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def reward_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["forge"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_weighting(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"quest_reward_shapes":quest_reward_shapes(),"impact_rewards":impact_rewards(),"counterfactual_shaping":counterfactual_shaping({"r":1}),"reward_events":reward_events("r",{}),"reward_routing":reward_routing("k",["r"]),"causal_weighting":causal_weighting({"r":1},{"r":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
