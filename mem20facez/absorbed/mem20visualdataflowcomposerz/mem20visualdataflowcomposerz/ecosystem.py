"""Cross-subsystem wiring for mem20visualdataflowcomposerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["blackboard_state","workcell_execute","output_compile","flow_events","flow_routing","causal_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20visualagentblackboardz","mem20autonomousworkcellsz","mem20agentoutputcompilerz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def blackboard_state()->dict:
    try:
        from mem20visualagentblackboardz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20visualagentblackboardz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20visualagentblackboardz","error":f"{type(exc).__name__}: {exc}"}
def workcell_execute()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,enqueue,cell_health
        c=create_cell("dataflow"); enqueue(c,{"op":"run"}); h=cell_health(c); return {"ok":True,"subsystem":"mem20autonomousworkcellsz","queued":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"ok":True,"node":"a"}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def flow_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("dataflow"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def flow_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["dataflow"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"blackboard_state":blackboard_state(),"workcell_execute":workcell_execute(),"output_compile":output_compile(),"flow_events":flow_events("f",{}),"flow_routing":flow_routing("k",["f"]),"causal_routing":causal_routing({"x":1},{"x":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
