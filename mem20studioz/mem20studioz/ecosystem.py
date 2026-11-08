"""Cross-subsystem wiring for mem20studioz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["audio_pipeline","rig_pipeline","production_pipeline","studio_events","studio_routing","workcell_dispatch","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20audiovoiceandmusicpipelinez","mem20rigginganimationandmotionpipelinez","mem20productionplanningandtaskorchestrationpipelinez","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20autonomousworkcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def audio_pipeline()->dict:
    try:
        from mem20audiovoiceandmusicpipelinez.domain import pipeline_report, probe as p
        r=pipeline_report(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20audiovoiceandmusicpipelinez","report":r is not None}
    except Exception:
        try:
            from mem20audiovoiceandmusicpipelinez.domain import probe as p
            r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20audiovoiceandmusicpipelinez","probe":r is not None}
        except Exception as exc: return {"ok":False,"subsystem":"mem20audiovoiceandmusicpipelinez","error":f"{type(exc).__name__}: {exc}"}
def rig_pipeline()->dict:
    try:
        from mem20rigginganimationandmotionpipelinez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20rigginganimationandmotionpipelinez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20rigginganimationandmotionpipelinez","error":f"{type(exc).__name__}: {exc}"}
def production_pipeline()->dict:
    try:
        from mem20productionplanningandtaskorchestrationpipelinez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20productionplanningandtaskorchestrationpipelinez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20productionplanningandtaskorchestrationpipelinez","error":f"{type(exc).__name__}: {exc}"}
def studio_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("studio"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def studio_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["studio"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def workcell_dispatch()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell,cell_health
        c=create_cell("studio"); h=cell_health(c); return {"ok":True,"subsystem":"mem20autonomousworkcellsz","health":h is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"audio_pipeline":audio_pipeline(),"rig_pipeline":rig_pipeline(),"production_pipeline":production_pipeline(),"studio_events":studio_events("s",{}),"studio_routing":studio_routing("k",["s"]),"workcell_dispatch":workcell_dispatch()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
