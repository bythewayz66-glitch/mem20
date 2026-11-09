"""Cross-subsystem wiring for mem20autonomousmicrosaasfoundryz.

Six peers chosen for the micro-SaaS foundry job (idea→MVP→launch→revenue) —
not a generic template. Failures reported, never fatal.
"""
from __future__ import annotations
import pathlib, sys
from typing import Mapping, Sequence

__all__ = ["economics", "demand_signal", "build_schedule", "launch_pipeline", "content_quality", "capability_routing", "probe"]
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PROJECTS = ("mem20simz","mem20demandforecastandcapacitybrainz","mem20aiproductionstudiooperatingsystemz","mem20autonomoussaleslaboratoryz","mem20loreragcontentgeneratorz","mem20capabilitymarketplacez")

def _bootstrap():
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path in sys.path: sys.path.remove(path)
        sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root not in sys.path: sys.path.append(root)
_bootstrap()

def economics(users:int, price:float, fixed:float=200.0, variable:float=1.0) -> dict:
    try:
        from mem20simz.domain import margin, profit, revenue, scenario_sim
        rev=revenue(users,price); cst=fixed+variable*users; prof=profit(rev,cst); mar=margin(rev,cst)
        scen=scenario_sim(max(1,users),price,fixed,variable,growth=0.1,periods=3)
        return {"ok":True,"subsystem":"mem20simz","revenue":rev,"profit":prof,"margin":mar,"scenario_periods":len(scen)}
    except Exception as exc:  # noqa: BLE001
        return {"ok":False,"subsystem":"mem20simz","error":f"{type(exc).__name__}: {exc}"}

def demand_signal(observations: Sequence[float]) -> dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        brain=DemandForecastAndCapacityBrain(alpha=0.3, window=max(5,len(observations) or 5))
        for v in (observations or [20,25,22,30,28]): brain.observe(v)
        fc=brain.forecast(steps=1)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":fc.get("point"),"high":fc.get("high"),"n":fc.get("n")}
    except Exception as exc:  # noqa: BLE001
        return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}

def build_schedule(features: Sequence[str], capacity:int=3) -> dict:
    try:
        from mem20aiproductionstudiooperatingsystemz.domain import resource_allocation, schedule_projects, studio_health
        projects=[{"id":f,"effort":1} for f in (features or ["core","auth","billing"])]
        sched=schedule_projects(projects, capacity)
        alloc=resource_allocation({f"slot-{i}":1 for i in range(max(1,capacity))}, [{"id":p["id"],"resource":"slot-0","amount":1,"priority":0} for p in projects])
        health=studio_health(projects, capacity)
        amap=alloc.get("allocations",alloc) if isinstance(alloc,dict) else {}
        return {"ok":True,"subsystem":"mem20aiproductionstudiooperatingsystemz","scheduled":len(sched) if isinstance(sched,list) else 0,"allocated":sum(1 for v in (amap.values() if isinstance(amap,dict) else []) if v),"health":float(health) if isinstance(health,(int,float)) else health}
    except Exception as exc:  # noqa: BLE001
        return {"ok":False,"subsystem":"mem20aiproductionstudiooperatingsystemz","error":f"{type(exc).__name__}: {exc}"}

def launch_pipeline(leads: Sequence[Mapping]) -> dict:
    try:
        from mem20autonomoussaleslaboratoryz.domain import conversion_probability, pipeline_value, segment_leads
        items=[dict(l) for l in leads] or [{"deal_value":29*12,"budget":500,"authority":True,"need":True,"timeline_days":14,"touches":1}]
        val=pipeline_value(items); conv=conversion_probability(items[0], items[0].get("touches",1)); seg=segment_leads(items)
        return {"ok":True,"subsystem":"mem20autonomoussaleslaboratoryz","pipeline_value":val,"conversion_probability":conv,"segments":{k:len(v) for k,v in seg.items()}}
    except Exception as exc:  # noqa: BLE001
        return {"ok":False,"subsystem":"mem20autonomoussaleslaboratoryz","error":f"{type(exc).__name__}: {exc}"}

def content_quality(prompt:str) -> dict:
    try:
        from mem20loreragcontentgeneratorz.domain import generate, quality_score, rank_adapters
        res=generate([{"text":"micro-saas landing context","source":"pipeline"}], prompt, adapter="foundry")
        ranked=rank_adapters([{"name":"foundry","score":0.9},{"name":"default","score":0.4}], prompt)
        q=quality_score(res.get("output",""), prompt)
        return {"ok":True,"subsystem":"mem20loreragcontentgeneratorz","adapter":ranked[0]["name"] if ranked else "default","quality":float(q) if isinstance(q,(int,float)) else 0.0,"output_len":len(str(res.get("output","")))}
    except Exception as exc:  # noqa: BLE001
        return {"ok":False,"subsystem":"mem20loreragcontentgeneratorz","error":f"{type(exc).__name__}: {exc}"}

def capability_routing(key:str, capabilities: Sequence[str]) -> dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); caps=list(capabilities) or ["auth","billing","hosting"]
        for c in caps: m.add(c)
        owner=m.locate(key); dist=m.distribution(keys=100)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":owner,"capabilities":len(caps),"distribution_keys":sum(dist.values()) if hasattr(dist,'values') else 100}
    except Exception as exc:  # noqa: BLE001
        return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def probe() -> dict:
    checks={"economics":economics(100,9.0),"demand_signal":demand_signal([20,25,22,30]),"build_schedule":build_schedule(["core","auth"]),"launch_pipeline":launch_pipeline([]),"content_quality":content_quality("launch micro-saas"),"capability_routing":capability_routing("foundry-1",["auth","billing"])}
    return {"ok": all(v.get("ok") for v in checks.values()), "checks": checks}
