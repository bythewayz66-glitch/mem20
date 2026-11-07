"""Cross-subsystem wiring for mem20compoundingproductecosystemz (6 peers, product-ecosystem specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["loyalty_graph","lifecycle_value","growth_economics","pipeline_signal","demand_signal","partnership_synergy","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20crossproductloyaltygraphz","mem20customerlifecycleenginez","mem20businessmodelsimulatorz","mem20autonomoussaleslaboratoryz","mem20demandforecastandcapacitybrainz","mem20acquisitionandpartnershipscoutz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def loyalty_graph(products:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score,recommend_products
        g={}; ps=list(products) or ["a","b"]
        for i in range(len(ps)-1): add_edge(g,ps[i],ps[i+1],1.0)
        rec=recommend_products(g,[ps[0]],top=2); score=loyalty_score([ps[0]],g)
        return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","recommendations":len(rec) if isinstance(rec,list) else 0,"loyalty_score":score}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}

def lifecycle_value()->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,lifetime_value,retention_probability
        c={"tenure_months":12,"spend":200,"events":10}; return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"ltv":lifetime_value(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}

def growth_economics(initial:float,rate:float,periods:int)->dict:
    try:
        from mem20businessmodelsimulatorz.domain import margin,profit,revenue,scenario_sim
        units=max(1,int(initial)); scen=scenario_sim(units,10.0,100.0,3.0,growth=rate,periods=max(2,periods))
        return {"ok":True,"subsystem":"mem20businessmodelsimulatorz","scenario_periods":len(scen),"final_profit":scen[-1]["profit"] if scen else 0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20businessmodelsimulatorz","error":f"{type(exc).__name__}: {exc}"}

def pipeline_signal(value:float)->dict:
    try:
        from mem20autonomoussaleslaboratoryz.domain import pipeline_value,segment_leads
        leads=[{"deal_value":value,"budget":value,"authority":True,"need":True,"timeline_days":20,"touches":1}]
        return {"ok":True,"subsystem":"mem20autonomoussaleslaboratoryz","pipeline_value":pipeline_value(leads),"segments":{k:len(v) for k,v in segment_leads(leads).items()}}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomoussaleslaboratoryz","error":f"{type(exc).__name__}: {exc}"}

def demand_signal(observations:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [100,110,120,115,130]): b.observe(v)
        fc=b.forecast(steps=1); return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":fc.get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}

def partnership_synergy()->dict:
    try:
        from mem20acquisitionandpartnershipscoutz.domain import strategic_fit,synergy_estimate
        t={"revenue":100,"markets":["saas"],"tech":["py"]}; u={"revenue":200,"markets":["saas"],"tech":["py"]}
        return {"ok":True,"subsystem":"mem20acquisitionandpartnershipscoutz","fit":strategic_fit(u,t),"synergy":synergy_estimate(u,t)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20acquisitionandpartnershipscoutz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"loyalty_graph":loyalty_graph(["a","b"]),"lifecycle_value":lifecycle_value(),"growth_economics":growth_economics(100,0.1,3),"pipeline_signal":pipeline_signal(1000),"demand_signal":demand_signal([100,110,120]),"partnership_synergy":partnership_synergy()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
