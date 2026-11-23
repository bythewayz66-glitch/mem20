"""Cross-subsystem wiring for mem20selfhealingplansz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["step_containment","healing_events","plan_routing","health_triggers","causal_repair","recovery_director","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20faultcontainmentcellsz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20universalhealthnervoussystemz","mem20causalroutingbrainz","mem20autonomousrecoverydirectorz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def step_containment(step:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"step":step,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","step":step,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","step":step,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def healing_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("healing"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def plan_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["heal"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def health_triggers(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for c in (list(components) or ["plan"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def causal_repair(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def recovery_director()->dict:
    try:
        from mem20autonomousrecoverydirectorz.domain import triage,recovery_report
        t=triage({"id":"p1","severity":2}); r=recovery_report(); return {"ok":True,"subsystem":"mem20autonomousrecoverydirectorz","triage":t is not None,"report_ok":r.get("ok")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousrecoverydirectorz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"step_containment":step_containment("s1"),"healing_events":healing_events("h",{}),"plan_routing":plan_routing("k",["h"]),"health_triggers":health_triggers(["plan"]),"causal_repair":causal_repair({"f":1},{"f":1}),"recovery_director":recovery_director()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
