"""Cross-subsystem wiring for mem20rewardforgez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["collective_intel","causal_routing","forge_events","forge_routing","forge_containment","software_foundry","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20collectivemodelintelligencez","mem20causalroutingbrainz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz","mem20autonomoussoftwarefoundryz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def collective_intel()->dict:
    try:
        from mem20collectivemodelintelligencez.domain import collective_report
        r=collective_report(); return {"ok":True,"subsystem":"mem20collectivemodelintelligencez","report":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20collectivemodelintelligencez","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def forge_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("modelforge"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def forge_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["forge"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def forge_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def software_foundry()->dict:
    try:
        from mem20autonomoussoftwarefoundryz.domain import foundry_report
        r=foundry_report(spec=None, code="def f(): return 1", metrics={"ok":True}); return {"ok":True,"subsystem":"mem20autonomoussoftwarefoundryz","report":r.get("ok") is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomoussoftwarefoundryz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"collective_intel":collective_intel(),"causal_routing":causal_routing({"q":1},{"q":1}),"forge_events":forge_events("f",{}),"forge_routing":forge_routing("k",["f"]),"forge_containment":forge_containment("f"),"software_foundry":software_foundry()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
