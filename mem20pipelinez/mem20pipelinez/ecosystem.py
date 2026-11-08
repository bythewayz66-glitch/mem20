"""Cross-subsystem wiring for mem20pipelinez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["automation_canvas","workcell_run","output_compile","pipeline_events","pipeline_routing","causal_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[3] if pathlib.Path(__file__).resolve().parents[2].name=="mem20pipelinez" else pathlib.Path(__file__).resolve().parents[2]
# _REPO_ROOT: inner pkg is mem20pipelinez/mem20pipelinez/ecosystem.py -> parents[2]=mem20pipelinez (top) -> parents[3]? no: file is .../mem20pipelinez/mem20pipelinez/ecosystem.py, parents[0]=mem20pipelinez(inner), parents[1]=mem20pipelinez(top), parents[2]=mem20(/opt/mem20)
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20personalautomationcanvasz","mem20autonomousworkcellsz","mem20agentoutputcompilerz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20causalroutingbrainz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def automation_canvas()->dict:
    try:
        from mem20personalautomationcanvasz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20personalautomationcanvasz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20personalautomationcanvasz","error":f"{type(exc).__name__}: {exc}"}
def workcell_run()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,enqueue,cell_health
        c=create_cell("pipelinez"); enqueue(c,{"stage":"build"}); h=cell_health(c)
        return {"ok":True,"subsystem":"mem20autonomousworkcellsz","health":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"stage":"ok"}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def pipeline_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("pipelinez"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def pipeline_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["pipeline"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"automation_canvas":automation_canvas(),"workcell_run":workcell_run(),"output_compile":output_compile(),"pipeline_events":pipeline_events("p",{}),"pipeline_routing":pipeline_routing("k",["p"]),"causal_routing":causal_routing({"x":1},{"x":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
