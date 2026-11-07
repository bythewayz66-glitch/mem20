"""Cross-subsystem wiring for mem20realtimeteampresencez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["presence_events","presence_routing","service_health","presence_containment","reconnect_plans","focus_context","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20universalhealthnervoussystemz","mem20faultcontainmentcellsz","mem20selfhealingplansz","mem20mixedinitiativefocusenginez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def presence_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("presence"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def presence_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["presence"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def service_health(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for c in (list(components) or ["presence"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def presence_containment(user:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"user":user,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","user":user,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","user":user,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def reconnect_plans(steps:Sequence[str])->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,plan_status
        p=create_plan(list(steps) or ["reconnect"]); return {"ok":True,"subsystem":"mem20selfhealingplansz","status":plan_status(p),"steps":len(list(steps) or ["reconnect"])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def focus_context(context:Mapping)->dict:
    try:
        from mem20mixedinitiativefocusenginez.domain import focus_score,suggest
        ctx=dict(context) or {"priority":1,"distractions":0}
        return {"ok":True,"subsystem":"mem20mixedinitiativefocusenginez","focus_score":focus_score(ctx),"suggestions":len(suggest(ctx,[{"label":"presence","priority":1},{"label":"status","priority":1}]))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20mixedinitiativefocusenginez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"presence_events":presence_events("p",{}),"presence_routing":presence_routing("u",["p"]),"service_health":service_health(["p"]),"presence_containment":presence_containment("u"),"reconnect_plans":reconnect_plans(["r"]),"focus_context":focus_context({"priority":1})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
