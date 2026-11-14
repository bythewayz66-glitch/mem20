"""Cross-subsystem wiring for mem20devicecapabilitycompilerz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["platform_context","artifact_placement","device_fleet","capability_match","compile_events","device_health","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20crossplatformmicrokernelz","mem20datalocalityoptimizerz","mem20zerotouchnodeswarmz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20universalhealthnervoussystemz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def platform_context()->dict:
    try:
        from mem20crossplatformmicrokernelz.domain import create_process,schedule
        procs=[create_process("compile",1),create_process("render",0)]; sched=schedule(procs)
        return {"ok":True,"subsystem":"mem20crossplatformmicrokernelz","scheduled_first":(sched[0].get("pid") if sched else None)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20crossplatformmicrokernelz","error":f"{type(exc).__name__}: {exc}"}
def artifact_placement(size_gb:float)->dict:
    try:
        from mem20datalocalityoptimizerz.domain import optimal_placement
        nodes=[{"id":"edge","latency_ms":1,"capacity_gb":20,"used_gb":0},{"id":"cloud","latency_ms":30,"capacity_gb":100,"used_gb":0}]
        p=optimal_placement({"id":"artifact","size_gb":max(0.001,size_gb)},nodes)
        return {"ok":True,"subsystem":"mem20datalocalityoptimizerz","placement":(p.get("id") if isinstance(p,dict) else None)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20datalocalityoptimizerz","error":f"{type(exc).__name__}: {exc}"}
def device_fleet(device_id:str)->dict:
    try:
        from mem20zerotouchnodeswarmz.domain import discover,register_node
        swarm={"nodes":[]}; register_node(swarm,{"id":device_id,"capacity":1,"availability":1.0,"capabilities":["compile"],"status":"ready"})
        return {"ok":True,"subsystem":"mem20zerotouchnodeswarmz","ready":len(discover(swarm))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20zerotouchnodeswarmz","error":f"{type(exc).__name__}: {exc}"}
def capability_match(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["compile"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def compile_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("compiler"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def device_health(device_ids:Sequence[str])->dict:
    try:
        from mem20universalhealthnervoussystemz.domain import check_all,overall,register_subsystem
        h={}
        for d in (list(device_ids) or ["d1"]): register_subsystem(h,d,lambda _d=d: {"ok":True,"device":_d})
        checked=check_all(h); return {"ok":True,"subsystem":"mem20universalhealthnervoussystemz","checked":len(checked) if isinstance(checked,(list,dict)) else 0,"overall":overall(h)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20universalhealthnervoussystemz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"platform_context":platform_context(),"artifact_placement":artifact_placement(0.1),"device_fleet":device_fleet("d1"),"capability_match":capability_match("k",["ml"]),"compile_events":compile_events("c",{}),"device_health":device_health(["d1"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
