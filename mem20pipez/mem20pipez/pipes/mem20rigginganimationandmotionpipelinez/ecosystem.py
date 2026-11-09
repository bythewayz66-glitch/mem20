"""Cross-subsystem wiring for mem20pipez (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["device_compile","data_locality","animation_events","pipeline_containment","capability_routing","config_validation","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20devicecapabilitycompilerz","mem20datalocalityoptimizerz","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20capabilitymarketplacez","mem20deterministicconfigurationgraphz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def device_compile(device:Mapping,code:str)->dict:
    try:
        from mem20devicecapabilitycompilerz.domain import detect_capabilities,compile_for_device
        caps=detect_capabilities(dict(device)); out=compile_for_device(code,caps)
        return {"ok":True,"subsystem":"mem20devicecapabilitycompilerz","compiled":out is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20devicecapabilitycompilerz","error":f"{type(exc).__name__}: {exc}"}
def data_locality(data,location:str)->dict:
    try:
        from mem20datalocalityoptimizerz.domain import placement_score,optimal_placement
        nodes=[{"id":location,"capacity":10},{"id":"remote","capacity":10}]
        score=placement_score(nodes[0],data if isinstance(data,dict) else {"v":data}); opt=optimal_placement(data if isinstance(data,dict) else {"v":data},nodes)
        return {"ok":True,"subsystem":"mem20datalocalityoptimizerz","score":score,"optimal":opt.get("id") if isinstance(opt,dict) else opt}
    except Exception as exc: return {"ok":False,"subsystem":"mem20datalocalityoptimizerz","error":f"{type(exc).__name__}: {exc}"}
def animation_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("animation"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def pipeline_containment(stage:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"stage":stage,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","stage":stage,"has_result":res is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","stage":stage,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def capability_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["animate"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def config_validation(cfg:Mapping)->dict:
    try:
        from mem20deterministicconfigurationgraphz.domain import add_node,validate
        g={}; add_node(g,"rig",dict(cfg)); v=validate(g); return {"ok":True,"subsystem":"mem20deterministicconfigurationgraphz","valid":v.get("valid")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20deterministicconfigurationgraphz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"device_compile":device_compile({"gpu":True},"shader"),"data_locality":data_locality({"bones":10},"local"),"animation_events":animation_events("a",{}),"pipeline_containment":pipeline_containment("rig"),"capability_routing":capability_routing("k",["a"]),"config_validation":config_validation({"name":"r"})}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
