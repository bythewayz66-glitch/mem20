"""Cross-subsystem wiring for mem20spatialcommanduniversez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["workcell_dispatch","causal_routing","spatial_events","spatial_routing","spatial_containment","spatial_health_peer","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20autonomousworkcellsz","mem20causalroutingbrainz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz","mem20universalhealthnervoussystemz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def workcell_dispatch()->dict:
    try:
        from mem20autonomousworkcellsz.domain import create_cell, enqueue, cell_health
        c=create_cell("spatial"); enqueue(c,{"op":"move"}); h=cell_health(c); return {"ok":True,"subsystem":"mem20autonomousworkcellsz","queued":h.get("queued",0)>=0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousworkcellsz","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def spatial_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("spatial"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def spatial_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["spatial"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def spatial_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def spatial_health_peer()->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}; register_subsystem(h,"spatial",lambda: {"ok":True}); checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"workcell_dispatch":workcell_dispatch(),"causal_routing":causal_routing({"d":1},{"d":1}),"spatial_events":spatial_events("s",{}),"spatial_routing":spatial_routing("k",["s"]),"spatial_containment":spatial_containment("s"),"spatial_health_peer":spatial_health_peer()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
