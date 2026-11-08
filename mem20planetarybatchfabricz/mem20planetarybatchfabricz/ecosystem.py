"""Cross-subsystem wiring for mem20planetarybatchfabricz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["roaming_scheduler","workcell_run","batch_events","batch_routing","autonomous_recovery","output_compile","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20roamingworkloadschedulerz","mem20autonomousworkcellsz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20autonomousrecoverydirectorz","mem20agentoutputcompilerz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def roaming_scheduler()->dict:
    try:
        from mem20roamingworkloadschedulerz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20roamingworkloadschedulerz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20roamingworkloadschedulerz","error":f"{type(exc).__name__}: {exc}"}
def workcell_run()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,enqueue,cell_health
        c=create_cell("batch"); enqueue(c,{"job":"run"}); h=cell_health(c)
        return {"ok":True,"subsystem":"mem20autonomousworkcellsz","health":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def batch_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("batch"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def batch_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["batch"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def autonomous_recovery()->dict:
    try:
        from mem20autonomousrecoverydirectorz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20autonomousrecoverydirectorz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousrecoverydirectorz","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"scheduled":True}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"roaming_scheduler":roaming_scheduler(),"workcell_run":workcell_run(),"batch_events":batch_events("b",{}),"batch_routing":batch_routing("k",["b"]),"autonomous_recovery":autonomous_recovery(),"output_compile":output_compile()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
