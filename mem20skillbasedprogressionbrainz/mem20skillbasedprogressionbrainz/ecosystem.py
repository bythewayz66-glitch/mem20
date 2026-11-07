"""Cross-subsystem wiring for mem20skillbasedprogressionbrainz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["skill_graph","motivation_twin","reward_forge","progression_events","progression_routing","progression_health_peer","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20dynamicskillgraphz","mem20playermotivationtwinz","mem20rewardforgez","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20universalhealthnervoussystemz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def skill_graph()->dict:
    try:
        from mem20dynamicskillgraphz.domain import add_skill, graph_stats
        g={}; add_skill(g,"s1"); st=graph_stats(g); return {"ok":True,"subsystem":"mem20dynamicskillgraphz","stats":st is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicskillgraphz","error":f"{type(exc).__name__}: {exc}"}
def motivation_twin()->dict:
    try:
        from mem20playermotivationtwinz.domain import create_twin, twin_health
        t=create_twin("p1"); h=twin_health(t); return {"ok":True,"subsystem":"mem20playermotivationtwinz","healthy":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20playermotivationtwinz","error":f"{type(exc).__name__}: {exc}"}
def reward_forge()->dict:
    try:
        from mem20rewardforgez.domain import linear_reward
        r=linear_reward({"xp":10},{"xp":1}); return {"ok":True,"subsystem":"mem20rewardforgez","reward":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20rewardforgez","error":f"{type(exc).__name__}: {exc}"}
def progression_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("progression"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def progression_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["progress"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def progression_health_peer()->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}; register_subsystem(h,"progression",lambda: {"ok":True}); checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"skill_graph":skill_graph(),"motivation_twin":motivation_twin(),"reward_forge":reward_forge(),"progression_events":progression_events("p",{}),"progression_routing":progression_routing("k",["p"]),"progression_health_peer":progression_health_peer()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
