"""Cross-subsystem wiring for mem20runtimecompatibilityenginez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["config_compat","capability_routing","compat_events","check_containment","healing_fixes","device_runtime","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20deterministicconfigurationgraphz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20selfhealingplansz","mem20devicecapabilitycompilerz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def config_compat(req:Mapping)->dict:
    try:
        from mem20deterministicconfigurationgraphz.domain import add_node,validate
        g={}; add_node(g,"runtime",dict(req)); v=validate(g); return {"ok":True,"subsystem":"mem20deterministicconfigurationgraphz","valid":v.get("valid")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20deterministicconfigurationgraphz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["compat"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def compat_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("compat"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def check_containment(check:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"check":check,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","check":check,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","check":check,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def healing_fixes(fixes:Sequence[str])->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,plan_status
        steps=list(fixes) or ["noop"]; p=create_plan(steps); return {"ok":True,"subsystem":"mem20selfhealingplansz","status":plan_status(p),"steps":len(steps)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def device_runtime(device:Mapping)->dict:
    try:
        from mem20devicecapabilitycompilerz.domain import detect_capabilities,compatibility
        caps=detect_capabilities(dict(device)); comp=compatibility(dict(device),[])
        return {"ok":True,"subsystem":"mem20devicecapabilitycompilerz","caps":len(caps) if isinstance(caps,(list,dict)) else 1,"compatible":comp.get("ok") if isinstance(comp,dict) else True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20devicecapabilitycompilerz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"config_compat":config_compat({"python":"3.11"}),"capability_routing":capability_routing("k",["c"]),"compat_events":compat_events("c",{}),"check_containment":check_containment("py"),"healing_fixes":healing_fixes(["install x"]),"device_runtime":device_runtime({"cpu":True})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
