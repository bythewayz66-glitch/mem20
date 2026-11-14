"""Cross-subsystem wiring for mem20visualagentblackboardz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["workcell_dispatch","output_compile","team_presence","episodic_memory","blackboard_events","blackboard_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomousworkcellsz","mem20agentoutputcompilerz","mem20realtimeteampresencez","mem20episodicmemorygraphz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def workcell_dispatch()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,cell_health
        c=create_cell("blackboard"); h=cell_health(c); return {"ok":True,"subsystem":"mem20autonomousworkcellsz","health":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"ok":True,"agent":"a1"}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def team_presence()->dict:
    try:
        from mem20realtimeteampresencez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20realtimeteampresencez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20realtimeteampresencez","error":f"{type(exc).__name__}: {exc}"}
def episodic_memory()->dict:
    try:
        from mem20episodicmemorygraphz.domain import create_episode,add_event,recall
        ep=create_episode("blackboard"); add_event(ep,{"text":"agent posted item"}); hits=recall([ep],"agent")
        return {"ok":True,"subsystem":"mem20episodicmemorygraphz","hits":len(hits) if isinstance(hits,(list,tuple)) else 1}
    except Exception as exc: return {"ok":False,"subsystem":"mem20episodicmemorygraphz","error":f"{type(exc).__name__}: {exc}"}
def blackboard_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("blackboard"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def blackboard_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["blackboard"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"workcell_dispatch":workcell_dispatch(),"output_compile":output_compile(),"team_presence":team_presence(),"episodic_memory":episodic_memory(),"blackboard_events":blackboard_events("b",{}),"blackboard_routing":blackboard_routing("k",["b"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
