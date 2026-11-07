"""Cross-subsystem wiring for mem20realitytosoftwarecompilerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["software_foundry","config_validation","compile_events","causal_routing","compile_containment","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomoussoftwarefoundryz","mem20deterministicconfigurationgraphz","mem20eventstreamsuperhighwayz","mem20causalroutingbrainz","mem20faultcontainmentcellsz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def software_foundry(spec:Mapping)->dict:
    try:
        from mem20autonomoussoftwarefoundryz.domain import foundry_report
        sp=dict(spec) if isinstance(spec,dict) else {"name":str(spec)}
        if "name" not in sp: sp["name"]="app"
        r=foundry_report(sp); return {"ok":True,"subsystem":"mem20autonomoussoftwarefoundryz","report_ok":r.get("ok")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomoussoftwarefoundryz","error":f"{type(exc).__name__}: {exc}"}
def config_validation(spec:Mapping)->dict:
    try:
        from mem20deterministicconfigurationgraphz.domain import add_node,validate
        g={}; add_node(g,"spec",dict(spec)); v=validate(g); return {"ok":True,"subsystem":"mem20deterministicconfigurationgraphz","valid":v.get("valid")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20deterministicconfigurationgraphz","error":f"{type(exc).__name__}: {exc}"}
def compile_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("compiler"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def compile_containment(name:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"compiled":name,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","name":name,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","name":name,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["compile"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"software_foundry":software_foundry({"name":"app"}),"config_validation":config_validation({"name":"app"}),"compile_events":compile_events("c",{}),"causal_routing":causal_routing({"q":1},{"q":1}),"compile_containment":compile_containment("app"),"capability_routing":capability_routing("k",["c"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
