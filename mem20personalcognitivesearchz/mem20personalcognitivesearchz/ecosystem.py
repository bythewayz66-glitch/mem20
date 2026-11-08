"""Cross-subsystem wiring for mem20personalcognitivesearchz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["episodic_memory","context_compress","predictive_recall","search_events","search_routing","output_compile","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20episodicmemorygraphz","mem20contextcompressionforgez","mem20predictiverecallenginez","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20agentoutputcompilerz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def episodic_memory()->dict:
    try:
        from mem20episodicmemorygraphz.domain import create_episode,add_event,recall as ep_recall
        ep=create_episode("search"); add_event(ep,{"text":"query hello"}); hits=ep_recall([ep],"hello")
        return {"ok":True,"subsystem":"mem20episodicmemorygraphz","hits":len(hits) if isinstance(hits,(list,tuple)) else 1}
    except Exception as exc: return {"ok":False,"subsystem":"mem20episodicmemorygraphz","error":f"{type(exc).__name__}: {exc}"}
def context_compress(text:str)->dict:
    try:
        from mem20contextcompressionforgez.domain import compress
        r=compress(text or "search", ratio=0.5); return {"ok":True,"subsystem":"mem20contextcompressionforgez","compressed":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20contextcompressionforgez","error":f"{type(exc).__name__}: {exc}"}
def predictive_recall()->dict:
    try:
        from mem20predictiverecallenginez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20predictiverecallenginez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20predictiverecallenginez","error":f"{type(exc).__name__}: {exc}"}
def search_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("cogsearch"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def search_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["search"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"ok":True}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"episodic_memory":episodic_memory(),"context_compress":context_compress("q"),"predictive_recall":predictive_recall(),"search_events":search_events("s",{}),"search_routing":search_routing("k",["s"]),"output_compile":output_compile()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
