"""Cross-subsystem wiring for mem20sensorymemoryingestz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["episodic_store","ingest_events","context_compression","ingest_routing","health_nervous","ingest_containment","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20episodicmemorygraphz","mem20eventstreamsuperhighwayz","mem20contextcompressionforgez","mem20capabilitymarketplacez","mem20universalhealthnervoussystemz","mem20faultcontainmentcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def episodic_store(title:str,data:Mapping)->dict:
    try:
        from mem20episodicmemorygraphz.domain import create_episode
        ep=create_episode(title, events=[dict(data)]); return {"ok":True,"subsystem":"mem20episodicmemorygraphz","id":ep.get("id") or ep.get("title")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20episodicmemorygraphz","error":f"{type(exc).__name__}: {exc}"}
def ingest_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("sensory"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def context_compression(text:str)->dict:
    try:
        from mem20contextcompressionforgez.domain import compress
        r=compress(text or "sensory", ratio=0.5); return {"ok":True,"subsystem":"mem20contextcompressionforgez","compressed":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20contextcompressionforgez","error":f"{type(exc).__name__}: {exc}"}
def ingest_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["ingest"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def health_nervous()->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}; register_subsystem(h,"sensory",lambda: {"ok":True}); checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def ingest_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"episodic_store":episodic_store("s",{"v":1}),"ingest_events":ingest_events("i",{}),"context_compression":context_compression("a"),"ingest_routing":ingest_routing("k",["i"]),"health_nervous":health_nervous(),"ingest_containment":ingest_containment("i")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
