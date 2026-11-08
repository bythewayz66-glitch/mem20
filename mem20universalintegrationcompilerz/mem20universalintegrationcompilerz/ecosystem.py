"""Cross-subsystem wiring for mem20universalintegrationcompilerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["protocol_discovery","runtime_compat","output_compile","integration_events","integration_routing","integration_containment","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20protocolautodiscoveryenginez","mem20runtimecompatibilityenginez","mem20agentoutputcompilerz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def protocol_discovery()->dict:
    try:
        from mem20protocolautodiscoveryenginez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20protocolautodiscoveryenginez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20protocolautodiscoveryenginez","error":f"{type(exc).__name__}: {exc}"}
def runtime_compat()->dict:
    try:
        from mem20runtimecompatibilityenginez.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20runtimecompatibilityenginez","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20runtimecompatibilityenginez","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"ok":True,"text":"integration"}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def integration_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("integration"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def integration_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["integration"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def integration_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"protocol_discovery":protocol_discovery(),"runtime_compat":runtime_compat(),"output_compile":output_compile(),"integration_events":integration_events("i",{}),"integration_routing":integration_routing("k",["i"]),"integration_containment":integration_containment("i")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
