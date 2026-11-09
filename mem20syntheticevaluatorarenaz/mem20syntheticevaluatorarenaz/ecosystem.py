"""Cross-subsystem wiring for mem20syntheticevaluatorarenaz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["collective_intel","counterfactual_eval","output_compile","arena_events","arena_routing","arena_containment","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20collectivemodelintelligencez","mem20simz","mem20agentoutputcompilerz","mem20eventstreamsuperhighwayz","mem20capabilitymarketplacez","mem20faultcontainmentcellsz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def collective_intel()->dict:
    try:
        from mem20collectivemodelintelligencez.domain import collective_report
        r=collective_report(); return {"ok":True,"subsystem":"mem20collectivemodelintelligencez","report":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20collectivemodelintelligencez","error":f"{type(exc).__name__}: {exc}"}
def counterfactual_eval()->dict:
    try:
        from mem20simz.domain import counterfactual,compare
        o={"s":1}; cf=counterfactual(o,{"change":{"s":2}}); return {"ok":True,"subsystem":"mem20simz","diff":len(compare(o,cf))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}
def output_compile()->dict:
    try:
        from mem20agentoutputcompilerz.domain import summarize
        r=summarize([{"ok":True}]); return {"ok":True,"subsystem":"mem20agentoutputcompilerz","summary":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20agentoutputcompilerz","error":f"{type(exc).__name__}: {exc}"}
def arena_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("arena"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def arena_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["eval"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def arena_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"collective_intel":collective_intel(),"counterfactual_eval":counterfactual_eval(),"output_compile":output_compile(),"arena_events":arena_events("a",{}),"arena_routing":arena_routing("k",["a"]),"arena_containment":arena_containment("a")}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
