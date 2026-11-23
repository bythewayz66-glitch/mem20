"""Cross-subsystem wiring for mem20zerotouchnodeswarmz (6 peers)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["workload_scheduler","edge_fleet","swarm_routing","swarm_events","swarm_containment","recovery_director","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20roamingworkloadschedulerz","mem20causalroutingbrainz","mem20capabilitymarketplacez","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20autonomousrecoverydirectorz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p); sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()
def workload_scheduler()->dict:
    try:
        from mem20roamingworkloadschedulerz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20roamingworkloadschedulerz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20roamingworkloadschedulerz","error":f"{type(exc).__name__}: {exc}"}
def edge_fleet()->dict:
    try:
        from mem20causalroutingbrainz.ecosystem import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20causalroutingbrainz","probe":r is not None}
    except Exception:
        try:
            from mem20causalroutingbrainz.domain import fleet_health
            r=fleet_health([],[]); return {"ok":True,"subsystem":"mem20causalroutingbrainz","health":r is not None}
        except Exception as exc: return {"ok":False,"subsystem":"mem20causalroutingbrainz","error":f"{type(exc).__name__}: {exc}"}
def swarm_routing(key:str,caps:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); cs=list(caps) or ["swarm"]
        for c in cs: m.add(c)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":m.locate(key),"capabilities":len(cs)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}
def swarm_events(name:str,payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("swarm"); publish(s,name,dict(payload)); return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":throughput(s)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}
def swarm_containment(op:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen,FaultContainmentCells
        cell=FaultContainmentCells(); res=cell.call(lambda: {"op":op,"ok":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"has_result":res is not None}
    except Exception as exc:
        if type(exc).__name__ == 'CircuitOpen':
            return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","op":op,"open":True}
        return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}
def recovery_director()->dict:
    try:
        from mem20autonomousrecoverydirectorz.domain import probe as p
        r=p(); return {"ok":bool(r.get("ok",True)),"subsystem":"mem20autonomousrecoverydirectorz","probe":r is not None}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousrecoverydirectorz","error":f"{type(exc).__name__}: {exc}"}
def probe()->dict:
    checks={"workload_scheduler":workload_scheduler(),"edge_fleet":edge_fleet(),"swarm_routing":swarm_routing("k",["s"]),"swarm_events":swarm_events("s",{}),"swarm_containment":swarm_containment("s"),"recovery_director":recovery_director()}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
