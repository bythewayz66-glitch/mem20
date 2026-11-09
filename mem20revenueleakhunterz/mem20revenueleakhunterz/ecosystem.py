"""Cross-subsystem wiring for mem20revenueleakhunterz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["revenue_economics","deal_pricing","leak_events","leak_containment","causal_analysis","hunter_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20simz","mem20autonomousdealdeskz","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20causalroutingbrainz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def revenue_economics(revenue:float,cost:float)->dict:
    try:
        from mem20simz.domain import margin,profit
        return {"ok":True,"subsystem":"mem20simz","profit":profit(revenue,cost),"margin":margin(revenue,cost)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def deal_pricing(amount:float)->dict:
    try:
        from mem20autonomousdealdeskz.domain import price_deal
        p=price_deal({"base_price":amount},{"segment":"standard"})
        return {"ok":True,"subsystem":"mem20autonomousdealdeskz","priced":p is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousdealdeskz","error":f"{type(exc).__name__}: {exc}"}
def leak_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("leaks"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def leak_containment(leak_id:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"leak":leak_id,"contained":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","leak":leak_id,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","leak":leak_id,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def causal_analysis(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def hunter_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["hunt"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"revenue_economics":revenue_economics(100,60),"deal_pricing":deal_pricing(50),"leak_events":leak_events("l",{}),"leak_containment":leak_containment("l1"),"causal_analysis":causal_analysis({"delta":1},{"delta":1}),"hunter_routing":hunter_routing("k",["h"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
