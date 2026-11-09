"""Cross-subsystem wiring for mem20simz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["causal_routing","scenario_events","recovery_paths","healing_alternatives","demand_scenarios","scenario_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20causalroutingbrainz","mem20eventstreamsuperhighwayz","mem20autonomousrecoverydirectorz","mem20selfhealingplansz","mem20demandforecastandcapacitybrainz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause,causal_effect
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights)),"effect":causal_effect([1,1],[0,0])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def scenario_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("counterfactual"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def recovery_paths(component:str)->dict:
    try:
        from mem20autonomousrecoverydirectorz.domain import rollback_plan,triage
        t=triage({"severity":"medium","component":component}); rb=rollback_plan({"version":2},{"version":1})
        return {"ok":True,"subsystem":"mem20autonomousrecoverydirectorz","priority":t.get("priority"),"rollback_steps":len(rb.get("steps",[]))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousrecoverydirectorz","error":f"{type(exc).__name__}: {exc}"}
def healing_alternatives(steps:Sequence[str])->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,plan_status
        p=create_plan(list(steps) or ["retry"]); return {"ok":True,"subsystem":"mem20selfhealingplansz","status":plan_status(p),"steps":len(list(steps) or ["retry"])}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def demand_scenarios(observations:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [10,12,11,13,14]): b.observe(v)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def scenario_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["sim"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"causal_routing":causal_routing({"x":1},{"x":1}),"scenario_events":scenario_events("cf",{}),"recovery_paths":recovery_paths("svc"),"healing_alternatives":healing_alternatives(["retry"]),"demand_scenarios":demand_scenarios([10,12]),"scenario_routing":scenario_routing("k",["sim"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
