"""Cross-subsystem wiring for mem20selfoptimizingkernelz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["causal_tuning","demand_forecast","counterfactual_eval","tuning_events","kernel_routing","tuning_containment","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20causalroutingbrainz","mem20demandforecastandcapacitybrainz","mem20counterfactualmemorysimulatorz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def causal_tuning(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def demand_forecast(obs:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(obs) or 5))
        for v in (obs or [1,1.1,1.2]): b.observe(v)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":b.forecast(1).get("point")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}
def counterfactual_eval(state:Mapping)->dict:
    try:
        from mem20counterfactualmemorysimulatorz.domain import counterfactual,compare
        o={"state":dict(state)}; cf=counterfactual(o,{"change":{"score":state.get("score",0)+1}}); return {"ok":True,"subsystem":"mem20counterfactualmemorysimulatorz","diff_keys":len(compare(o,cf))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20counterfactualmemorysimulatorz","error":f"{type(exc).__name__}: {exc}"}
def tuning_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("kernel"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def kernel_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["optimize"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def tuning_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"causal_tuning":causal_tuning({"s":1},{"s":1}),"demand_forecast":demand_forecast([1,2]),"counterfactual_eval":counterfactual_eval({"score":1}),"tuning_events":tuning_events("t",{}),"kernel_routing":kernel_routing("k",["o"]),"tuning_containment":tuning_containment("opt")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
