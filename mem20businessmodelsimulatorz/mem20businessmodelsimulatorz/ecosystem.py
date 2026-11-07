"""Cross-subsystem wiring for mem20businessmodelsimulatorz (6 peers, business-model specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["demand_signal","counterfactual_scenarios","partnership_synergy","lifecycle_value","loyalty_graph","pipeline_signal","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20demandforecastandcapacitybrainz","mem20counterfactualmemorysimulatorz","mem20acquisitionandpartnershipscoutz","mem20customerlifecycleenginez","mem20crossproductloyaltygraphz","mem20autonomoussaleslaboratoryz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p)
        sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def demand_signal(observations:Sequence[float], capacity:int=100)->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [50,55,60,58,62]): b.observe(v)
        fc=b.forecast(steps=1); headroom=b.capacity_for(capacity)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":fc.get("point"),"headroom":headroom}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}

def counterfactual_scenarios(base:Mapping, intervention:Mapping)->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import compare, counterfactual, outcome_probability
        orig={"state": dict(base), "base_rate": 0.5}
        iv=dict(intervention); cf=counterfactual(orig, {"change": iv.get("change", {"price": iv.get("delta", 0.1)})})
        comp=compare(orig,cf)
        prob=outcome_probability(orig, {"effect": float(iv.get("effect", 0.1))})
        return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","diff_keys":len(comp) if isinstance(comp,dict) else 0,"outcome_probability":prob}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}

def partnership_synergy(target:Mapping, us:Mapping)->dict:
    try:
        from mem20acquisitionandpartnershipscoutz.domain import strategic_fit, synergy_estimate, target_score
        t=dict(target); u=dict(us)
        fit=strategic_fit(u,t); syn=synergy_estimate(u,t)
        criteria={"weights":{"revenue":1.0},"targets":{"revenue":max(1.0,float(t.get("revenue",100) or 100))}}
        score=target_score(t,criteria)
        return {"ok":True,"subsystem":"mem20acquisitionandpartnershipscoutz","fit":fit,"synergy":syn,"target_score":score}
    except Exception as exc: return {"ok":False,"subsystem":"mem20acquisitionandpartnershipscoutz","error":f"{type(exc).__name__}: {exc}"}

def lifecycle_value(customer:Mapping)->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage, lifetime_value, retention_probability
        c=dict(customer); stage=lifecycle_stage(c); ltv=lifetime_value(c); ret=retention_probability(c)
        return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":stage,"ltv":ltv,"retention":ret}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}

def loyalty_graph(user_products:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge, centrality, loyalty_score, recommend_products
        g={}; add_edge(g,"core","addon",1.0); add_edge(g,"core","pro",0.8); ups=list(user_products) or ["core"]
        rec=recommend_products(g,ups,top=2); score=loyalty_score(ups,g); cent=centrality(g)
        return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","recommendations":len(rec) if isinstance(rec,list) else 0,"loyalty_score":score,"centrality_keys":len(cent) if isinstance(cent,dict) else 0}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}

def pipeline_signal(leads:Sequence[Mapping])->dict:
    try:
        from mem20autonomoussaleslaboratoryz.domain import conversion_probability, pipeline_value, segment_leads
        ls=list(leads) or [{"deal_value":1000,"budget":2000,"authority":True,"need":True,"timeline_days":10,"touches":1}]
        val=pipeline_value(ls); conv=conversion_probability(ls[0], ls[0].get("touches",1)); seg=segment_leads(ls)
        return {"ok":True,"subsystem":"mem20autonomoussaleslaboratoryz","pipeline_value":val,"sample_conversion":conv,"segments": {k:len(v) for k,v in seg.items()}}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomoussaleslaboratoryz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"demand_signal":demand_signal([50,55,60]),"counterfactual_scenarios":counterfactual_scenarios({"price":10,"units":100},{"action":"price_up","delta":0.1}),"partnership_synergy":partnership_synergy({"revenue":100},{"revenue":200}),"lifecycle_value":lifecycle_value({"tenure_months":6,"spend":100}),"loyalty_graph":loyalty_graph(["core"]),"pipeline_signal":pipeline_signal([])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
