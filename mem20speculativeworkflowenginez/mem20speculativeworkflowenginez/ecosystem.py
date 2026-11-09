"""Cross-subsystem wiring for mem20speculativeworkflowenginez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["counterfactual_branch","causal_routing","workflow_events","workflow_routing","branch_containment","self_healing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20simz","mem20causalroutingbrainz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz","mem20selfhealingplansz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def counterfactual_branch()->dict:
    try:
        from mem20simz.domain import counterfactual,compare
        o={"w":1}; cf=counterfactual(o,{"change":{"w":2}}); return {"ok":True,"subsystem":"mem20simz","diff":len(compare(o,cf))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def causal_routing(features:Mapping,weights:Mapping)->dict:
    try:
        from mem20causalroutingbrainz.domain import route_by_cause
        return {"ok":True,"subsystem":"mem20causalroutingbrainz","route_score":route_by_cause(dict(features),dict(weights))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def workflow_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("speculative"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def workflow_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["speculate"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def branch_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def self_healing()->dict:
    try:
        from mem20selfhealingplansz.domain import create_plan,execute_step,plan_status
        p=create_plan(["x"]); execute_step(p,0,lambda n: None); st=plan_status(p); return {"ok":True,"subsystem":"mem20selfhealingplansz","done":st.get("done",0)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20selfhealingplansz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"counterfactual_branch":counterfactual_branch(),"causal_routing":causal_routing({"b":1},{"b":1}),"workflow_events":workflow_events("w",{}),"workflow_routing":workflow_routing("k",["w"]),"branch_containment":branch_containment("w"),"self_healing":self_healing()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
