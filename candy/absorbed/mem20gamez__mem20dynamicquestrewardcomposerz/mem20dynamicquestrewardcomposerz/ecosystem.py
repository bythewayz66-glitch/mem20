"""Cross-subsystem wiring for mem20dynamicquestrewardcomposerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["challenge_context","narrative_hooks","quest_events","loyalty_rewards","capability_routing","lifecycle_retention","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20communitychallengeenginez","mem20dynamicnarrativeenginez","mem20eventstreamsuperhighwayz","mem20crossproductloyaltygraphz","mem20capabilitymarketplacez","mem20customerlifecycleenginez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def challenge_context()->dict:
    try:
        from mem20communitychallengeenginez.domain import challenge_report
        r=challenge_report("quest",5,["p1","p2"],100.0); return {"ok":True,"subsystem":"mem20communitychallengeenginez","report_ok":r.get("ok")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20communitychallengeenginez","error":f"{type(exc).__name__}: {exc}"}
def narrative_hooks()->dict:
    try:
        from mem20dynamicnarrativeenginez.domain import create_story,add_node
        s=create_story("q"); add_node(s,"q","Quest begins",[]); return {"ok":True,"subsystem":"mem20dynamicnarrativeenginez","nodes":len(s.get("nodes",{}))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicnarrativeenginez","error":f"{type(exc).__name__}: {exc}"}
def quest_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("quests"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def loyalty_rewards(products:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score
        g={}; add_edge(g,"quest","reward",1.0); ps=list(products) or ["quest"]; return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","loyalty_score":loyalty_score(ps,g)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["reward"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def lifecycle_retention()->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,retention_probability
        c={"days_since_signup":20,"purchases":2,"engagement":0.6,"recency_days":5}; return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"challenge_context":challenge_context(),"narrative_hooks":narrative_hooks(),"quest_events":quest_events("q",{}),"loyalty_rewards":loyalty_rewards(["quest"]),"capability_routing":capability_routing("k",["r"]),"lifecycle_retention":lifecycle_retention()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
