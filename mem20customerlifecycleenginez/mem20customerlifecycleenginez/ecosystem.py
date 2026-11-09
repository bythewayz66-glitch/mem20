"""Cross-subsystem wiring for mem20customerlifecycleenginez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["business_value","pipeline_signal","loyalty_context","demand_signal","lifecycle_events","growth_partnerships","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20simz","mem20autonomoussaleslaboratoryz","mem20crossproductloyaltygraphz","mem20demandforecastandcapacitybrainz","mem20eventstreamsuperhighwayz","mem20acquisitionandpartnershipscoutz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def business_value(ltv:float)->dict:
    try:
        from mem20simz.domain import margin,profit,revenue
        r=revenue(max(1,int(ltv/10)),10.0); c=r*0.4; return {"ok":True,"subsystem":"mem20simz","revenue":r,"profit":profit(r,c),"margin":margin(r,c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def pipeline_signal(ltv:float)->dict:
    try:
        from mem20autonomoussaleslaboratoryz.domain import pipeline_value,segment_leads
        leads=[{"deal_value":ltv,"budget":ltv,"authority":True,"need":True,"timeline_days":20,"touches":1}]
        return {"ok":True,"subsystem":"mem20autonomoussaleslaboratoryz","pipeline_value":pipeline_value(leads),"segments":{k:len(v) for k,v in segment_leads(leads).items()}}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomoussaleslaboratoryz","error":f"{type(exc).__name__}: {exc}"}
def loyalty_context(products:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score,recommend_products
        g={}; add_edge(g,"core","pro",1.0); ps=list(products) or ["core"]; return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","loyalty_score":loyalty_score(ps,g),"recommendations":len(recommend_products(g,ps,2))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}
def demand_signal(obs:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [10,12,11,13]): b.observe(v)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def lifecycle_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("lifecycle"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def growth_partnerships()->dict:
    try:
        from mem20acquisitionandpartnershipscoutz.domain import strategic_fit,synergy_estimate
        t={"revenue":100,"markets":["saas"],"tech":["py"]}; u={"revenue":150,"markets":["saas"],"tech":["py"]}; return {"ok":True,"subsystem":"mem20acquisitionandpartnershipscoutz","fit":strategic_fit(u,t),"synergy":synergy_estimate(u,t)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20acquisitionandpartnershipscoutz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"business_value":business_value(100),"pipeline_signal":pipeline_signal(100),"loyalty_context":loyalty_context(["core"]),"demand_signal":demand_signal([10,12]),"lifecycle_events":lifecycle_events("e",{}),"growth_partnerships":growth_partnerships()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
