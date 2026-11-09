"""Cross-subsystem wiring for mem20twinz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["lifecycle_signal","counterfactual_scenarios","demand_signal","loyalty_context","twin_events","capability_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20customerlifecycleenginez","mem20simz","mem20causalroutingbrainz","mem20crossproductloyaltygraphz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def lifecycle_signal(customer:Mapping)->dict:
    try:
        from mem20customerlifecycleenginez.domain import lifecycle_stage,lifetime_value,retention_probability
        c=dict(customer); return {"ok":True,"subsystem":"mem20customerlifecycleenginez","stage":lifecycle_stage(c),"ltv":lifetime_value(c),"retention":retention_probability(c)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20customerlifecycleenginez","error":f"{type(exc).__name__}: {exc}"}
def counterfactual_scenarios(state:Mapping)->dict:
    try:
        from mem20simz.domain import counterfactual,outcome_probability,compare
        orig={"state":dict(state),"base_rate":0.5}; cf=counterfactual(orig,{"change":{"engagement":0.8}}); diff=compare(orig,cf); prob=outcome_probability(orig,{"effect":0.2})
        return {"ok":True,"subsystem":"mem20simz","diff_keys":len(diff),"outcome_probability":prob}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def demand_signal(observations:Sequence[float])->dict:
    try:
        from mem20causalroutingbrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [5,6,7,6,8]): b.observe(v)
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def loyalty_context(products:Sequence[str])->dict:
    try:
        from mem20crossproductloyaltygraphz.domain import add_edge,loyalty_score,recommend_products
        g={}; add_edge(g,"core","addon",1.0); ps=list(products) or ["core"]; rec=recommend_products(g,ps,2); score=loyalty_score(ps,g)
        return {"ok":True,"subsystem":"mem20crossproductloyaltygraphz","recommendations":len(rec),"loyalty_score":score}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossproductloyaltygraphz","error":f"{type(exc).__name__}: {exc}"}
def twin_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("twins"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["predict"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"lifecycle_signal":lifecycle_signal({"tenure_months":6,"spend":100}),"counterfactual_scenarios":counterfactual_scenarios({"engagement":0.5}),"demand_signal":demand_signal([5,6,7]),"loyalty_context":loyalty_context(["core"]),"twin_events":twin_events("t",{}),"capability_routing":capability_routing("k",["p"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
