"""Cross-subsystem wiring for mem20resourceexchangemarketz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["market_routing","trade_events","trade_containment","demand_pricing","trade_economics","participant_loyalty","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20demandforecastandcapacitybrainz","mem20businessmodelsimulatorz","mem20crossproductloyaltygraphz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def market_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["trade"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def trade_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("market"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def trade_containment(trade_id:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"trade":trade_id,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","trade":trade_id,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","trade":trade_id,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def demand_pricing(obs:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [1,1.2,1.1]): b.observe(v)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def trade_economics(revenue:float,cost:float)->dict:
    try:
        from mem20businessmodelsimulatorz.domain import margin,profit
        return {"ok":True,"subsystem":"mem20businessmodelsimulatorz","profit":profit(revenue,cost),"margin":margin(revenue,cost)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20businessmodelsimulatorz","error":f"{type(exc).__name__}: {exc}"}
def participant_loyalty(users:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score
        g={}; us=list(users) or ["a"]
        if len(us)>=2: add_edge(g,us[0],us[1],1.0)
        return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","loyalty_score":loyalty_score(us[:1],g)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"market_routing":market_routing("cpu",["t"]),"trade_events":trade_events("t",{}),"trade_containment":trade_containment("t1"),"demand_pricing":demand_pricing([1,2]),"trade_economics":trade_economics(10,4),"participant_loyalty":participant_loyalty(["a","b"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
