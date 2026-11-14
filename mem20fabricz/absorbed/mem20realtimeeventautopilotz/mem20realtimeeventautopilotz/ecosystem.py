"""Cross-subsystem wiring for mem20realtimeeventautopilotz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["stream_backbone","action_containment","healing_actions","causal_decisions","health_triggers","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20selfhealingplansz","mem20causalroutingbrainz","mem20universalhealthnervoussystemz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def stream_backbone(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("autopilot"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def action_containment(action:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"action":action,"ran":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","action":action,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","action":action,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def healing_actions(steps:Sequence[str])->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,plan_status
        p=create_plan(list(steps) or ["mitigate"]); return {"ok":True,"subsystem":"mem20selfhealingplansz","status":plan_status(p),"steps":len(list(steps) or ["mitigate"])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def causal_decisions(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def health_triggers(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for c in (list(components) or ["events"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["action"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"stream_backbone":stream_backbone("e",{}),"action_containment":action_containment("notify"),"healing_actions":healing_actions(["restart"]),"causal_decisions":causal_decisions({"sev":1},{"sev":1}),"health_triggers":health_triggers(["svc"]),"capability_routing":capability_routing("k",["a"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
