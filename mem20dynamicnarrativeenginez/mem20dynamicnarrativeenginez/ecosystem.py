"""Cross-subsystem wiring for mem20dynamicnarrativeenginez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["narrative_events","challenge_hooks","context_compression","focus_guidance","capability_routing","branching_scenarios","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20eventstreamsuperhighwayz","mem20communitychallengeenginez","mem20contextcompressionforgez","mem20mixedinitiativefocusenginez","mem20capabilitymarketplacez","mem20counterfactualmemorysimulatorz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def narrative_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("narrative"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def challenge_hooks()->dict:
    try:
        from mem20communitychallengeenginez.domain import challenge_report
        r=challenge_report("story",3,["p1"],30.0); return {"ok":True,"subsystem":"mem20communitychallengeenginez","report_ok":r.get("ok")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20communitychallengeenginez","error":f"{type(exc).__name__}: {exc}"}
def context_compression(text:str)->dict:
    try:
        from mem20contextcompressionforgez.domain import compress,compression_ratio
        c=compress(text or "Once upon a time in a dynamic narrative.", 0.5); return {"ok":True,"subsystem":"mem20contextcompressionforgez","ratio":compression_ratio(text or "Once upon a time in a dynamic narrative.", c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20contextcompressionforgez","error":f"{type(exc).__name__}: {exc}"}
def focus_guidance(context:Mapping)->dict:
    try:
        from mem20mixedinitiativefocusenginez.domain import focus_score,suggest
        ctx=dict(context) or {"goal":"narrative","distractions":1,"priority":1}; return {"ok":True,"subsystem":"mem20mixedinitiativefocusenginez","focus_score":focus_score(ctx),"suggestions":len(suggest(ctx,[{"label":"continue","priority":2},{"label":"branch","priority":1},{"label":"summarize","priority":1}]))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20mixedinitiativefocusenginez","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["story"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def branching_scenarios(state:Mapping)->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import branch,counterfactual
        mem={"state":dict(state) or {"chapter":1},"branch":0}; b=branch(mem,{"chapter":2}); cf=counterfactual(mem,{"change":{"ending":"alt"}})
        return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","branch":b.get("branch"),"has_cf":bool(cf.get("state"))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"narrative_events":narrative_events("n",{}),"challenge_hooks":challenge_hooks(),"context_compression":context_compression("hello world story"),"focus_guidance":focus_guidance({"goal":"x","priority":1}),"capability_routing":capability_routing("k",["s"]),"branching_scenarios":branching_scenarios({"c":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
