"""Cross-subsystem wiring for mem20autonomoussoftwarefoundryz (6 peers, software-foundry specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["capability_routing","artifact_recovery","build_events","deploy_containment","spec_quality","effort_economics","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20capabilitymarketplacez","mem20pipez","mem20eventstreamsuperhighwayz","mem20faultcontainmentcellsz","mem20loreragcontentgeneratorz","mem20businessmodelsimulatorz")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p)
        sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def capability_routing(key:str, tools:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); caps=list(tools) or ["lint","test","deploy"]
        for c in caps: m.add(c)
        owner=m.locate(key); dist=m.distribution(keys=100)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":owner,"tools":len(caps),"distribution_keys":sum(dist.values()) if hasattr(dist,'values') else 100}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def artifact_recovery(artifact_id:str)->dict:
    try:
        from mem20pipez.domain import recover,version_asset,vc_health
        versions=[version_asset(artifact_id,"src-v1"), version_asset(artifact_id,"src-v2")]
        rec=recover(versions,"src-v1"); health=vc_health(versions)
        return {"ok":True,"subsystem":"mem20pipez","recovered":rec,"versions":len(versions),"health":health}
    except Exception as exc: return {"ok":False,"subsystem":"mem20pipez","error":f"{type(exc).__name__}: {exc}"}

def build_events(name:str, payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("software-foundry"); publish(s,name,dict(payload)); tp=throughput(s)
        return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":tp}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def deploy_containment(component:str)->dict:
    try:
        from mem20faultcontainmentcellsz.domain import CircuitOpen, FaultContainmentCells
        cell=FaultContainmentCells()
        result=cell.call(lambda: {"deployed":True})
        return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","component":component,"has_result":result is not None}
    except CircuitOpen: return {"ok":True,"subsystem":"mem20faultcontainmentcellsz","component":component,"open":True}
    except Exception as exc: return {"ok":False,"subsystem":"mem20faultcontainmentcellsz","error":f"{type(exc).__name__}: {exc}"}

def spec_quality(prompt:str)->dict:
    try:
        from mem20loreragcontentgeneratorz.domain import generate,quality_score,rank_adapters
        res=generate([{"text":"software spec context","source":"foundry"}],prompt,adapter="spec")
        ranked=rank_adapters([{"name":"spec","score":0.9},{"name":"default","score":0.4}],prompt)
        q=quality_score(res.get("output",""),prompt)
        return {"ok":True,"subsystem":"mem20loreragcontentgeneratorz","adapter":ranked[0]["name"] if ranked else "default","quality":float(q) if isinstance(q,(int,float)) else 0.0,"output_len":len(str(res.get("output","")))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20loreragcontentgeneratorz","error":f"{type(exc).__name__}: {exc}"}

def effort_economics(days:int, rate:float=500.0)->dict:
    try:
        from mem20businessmodelsimulatorz.domain import margin,profit,revenue,scenario_sim
        units=max(1,days); rev=revenue(units,rate); cst=units*rate*0.6; prof=profit(rev,cst); mar=margin(rev,cst)
        scen=scenario_sim(units,rate,cst*0.2,rate*0.1,growth=0.05,periods=2)
        return {"ok":True,"subsystem":"mem20businessmodelsimulatorz","profit":prof,"margin":mar,"scenario_periods":len(scen)}
    except Exception as exc: return {"ok":False,"subsystem":"mem20businessmodelsimulatorz","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"capability_routing":capability_routing("build-1",["lint","test"]),"artifact_recovery":artifact_recovery("app"),"build_events":build_events("build.ok",{"id":"b1"}),"deploy_containment":deploy_containment("deploy"),"spec_quality":spec_quality("build api"),"effort_economics":effort_economics(6)}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
