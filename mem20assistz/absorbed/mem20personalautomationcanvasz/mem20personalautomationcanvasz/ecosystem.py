"""Cross-subsystem wiring for mem20personalautomationcanvasz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["workcell_run","output_compile","self_healing","canvas_events","canvas_routing","causal_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomousworkcellsz","mem20agentoutputcompilerz","mem20selfhealingplansz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def workcell_run()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,enqueue,cell_health
        c=create_cell("canvas"); enqueue(c,{"wf":"run"}); h=cell_health(c); return {"ok":True,"subsystem":"mem20autonomousworkcellsz","health":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"ok":True}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def self_healing()->dict:
    try:
        from mem20selfhealingplansz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20selfhealingplansz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def canvas_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("canvas"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def canvas_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["canvas"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"workcell_run":workcell_run(),"output_compile":output_compile(),"self_healing":self_healing(),"canvas_events":canvas_events("c",{}),"canvas_routing":canvas_routing("k",["c"]),"causal_routing":causal_routing({"x":1},{"x":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
