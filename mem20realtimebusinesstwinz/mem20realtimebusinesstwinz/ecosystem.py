"""Cross-subsystem wiring for mem20realtimebusinesstwinz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["business_scenarios","kpi_forecast","kpi_events","health_alerts","counterfactual_scenarios","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20simz","mem20demandforecastandcapacitybrainz","mem20eventstreamsuperhighwayz","mem20universalhealthnervoussystemz","mem20simz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def business_scenarios(revenue:float)->dict:
    try:
        from mem20simz.domain import margin,profit
        c=revenue*0.6; return {"ok":True,"subsystem":"mem20simz","profit":profit(revenue,c),"margin":margin(revenue,c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def kpi_forecast(obs:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [10,12,11,13]): b.observe(v)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def kpi_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("biztwin"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def health_alerts(components:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for c in (list(components) or ["kpi"]): register_subsystem(h,c,lambda _c=c: {"ok":True,"component":_c})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def counterfactual_scenarios(state:Mapping)->dict:
    try:
        from mem20simz.domain import counterfactual,compare
        orig={"state":dict(state) or {"rev":100}}; cf=counterfactual(orig,{"change":{"rev":120}}); diff=compare(orig,cf)
        return {"ok":True,"subsystem":"mem20simz","diff_keys":len(diff)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["twin"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"business_scenarios":business_scenarios(100),"kpi_forecast":kpi_forecast([10,12]),"kpi_events":kpi_events("k",{}),"health_alerts":health_alerts(["kpi"]),"counterfactual_scenarios":counterfactual_scenarios({"rev":100}),"capability_routing":capability_routing("k",["t"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
