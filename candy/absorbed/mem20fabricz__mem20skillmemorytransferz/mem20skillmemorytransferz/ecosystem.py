"""Cross-subsystem wiring for mem20skillmemorytransferz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["skill_graph","episodic_memory","memory_timemachine","transfer_events","transfer_routing","transfer_containment","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20dynamicskillgraphz","mem20episodicmemorygraphz","mem20memorytimemachinez","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def skill_graph()->dict:
    try:
        from mem20dynamicskillgraphz.domain import add_skill,graph_stats
        g={}; add_skill(g,"s1"); return {"ok":True,"subsystem":"mem20dynamicskillgraphz","stats":graph_stats(g) is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20dynamicskillgraphz","error":f"{type(exc).__name__}: {exc}"}
def episodic_memory()->dict:
    try:
        from mem20episodicmemorygraphz.domain import create_episode
        ep=create_episode("transfer",[{"skill":"s1"}]); return {"ok":True,"subsystem":"mem20episodicmemorygraphz","id":ep.get("id") or ep.get("title")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20episodicmemorygraphz","error":f"{type(exc).__name__}: {exc}"}
def memory_timemachine()->dict:
    try:
        from mem20memorytimemachinez.domain import snapshot,rewind
        s=snapshot({"skills":{"s1":1}}); r=rewind([s], 0); return {"ok":True,"subsystem":"mem20memorytimemachinez","restored":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20memorytimemachinez","error":f"{type(exc).__name__}: {exc}"}
def transfer_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("transfer"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def transfer_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["transfer"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def transfer_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"skill_graph":skill_graph(),"episodic_memory":episodic_memory(),"memory_timemachine":memory_timemachine(),"transfer_events":transfer_events("t",{}),"transfer_routing":transfer_routing("k",["t"]),"transfer_containment":transfer_containment("t")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
