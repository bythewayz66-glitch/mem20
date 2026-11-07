"""Cross-subsystem wiring for mem20autonomoussaleslaboratoryz (6 peers, sales-lab specific)."""
from __future__ import annotations
import pathlib,sys
from typing import Mapping,Sequence
__all__=["content_outreach","spam_guardrail","demand_timing","experiment_events","deal_handoff","channel_routing","probe"]
_REPO_ROOT=pathlib.Path(__file__).resolve().parents[2]
_PROJECTS=("mem20loreragcontentgeneratorz","mem20antiexploitationrewardshieldz","mem20demandforecastandcapacitybrainz","mem20eventstreamsuperhighwayz","mem20autonomousdealdeskz","mem20capabilitymarketplacez")
def _bootstrap():
    for name in reversed(_PROJECTS):
        p=str(_REPO_ROOT/name)
        if p in sys.path: sys.path.remove(p)
        sys.path.insert(0,p)
    r=str(_REPO_ROOT)
    if r not in sys.path: sys.path.append(r)
_bootstrap()

def content_outreach(prompt:str)->dict:
    try:
        from mem20loreragcontentgeneratorz.domain import generate,quality_score,rank_adapters
        res=generate([{"text":"sales outreach context","source":"lab"}],prompt,adapter="outreach")
        ranked=rank_adapters([{"name":"outreach","score":0.9},{"name":"default","score":0.4}],prompt)
        q=quality_score(res.get("output",""),prompt)
        return {"ok":True,"subsystem":"mem20loreragcontentgeneratorz","adapter":ranked[0]["name"] if ranked else "default","quality":float(q) if isinstance(q,(int,float)) else 0.0,"output_len":len(str(res.get("output","")))}
    except Exception as exc: return {"ok":False,"subsystem":"mem20loreragcontentgeneratorz","error":f"{type(exc).__name__}: {exc}"}

def spam_guardrail(send_attempt:float, state:Mapping, approved:bool)->dict:
    try:
        from mem20antiexploitationrewardshieldz.domain import RewardShield
        shield=RewardShield(corroboration_tolerance=1.0,window=5,hard_clamp=1.0)
        res=shield.evaluate(send_attempt, dict(state), progress_evidence=approved)
        return {"ok":True,"subsystem":"mem20antiexploitationrewardshieldz","paid":res.get("paid"),"reason":res.get("reason"),"exploit_ratio":shield.exploit_ratio()}
    except Exception as exc: return {"ok":False,"subsystem":"mem20antiexploitationrewardshieldz","error":f"{type(exc).__name__}: {exc}"}

def demand_timing(observations:Sequence[float])->dict:
    try:
        from mem20demandforecastandcapacitybrainz.domain import DemandForecastAndCapacityBrain
        b=DemandForecastAndCapacityBrain(alpha=0.3,window=max(5,len(observations) or 5))
        for v in (observations or [5,6,8,7,9]): b.observe(v)
        fc=b.forecast(steps=1)
        return {"ok":True,"subsystem":"mem20demandforecastandcapacitybrainz","point":fc.get("point"),"high":fc.get("high"),"n":fc.get("n")}
    except Exception as exc: return {"ok":False,"subsystem":"mem20demandforecastandcapacitybrainz","error":f"{type(exc).__name__}: {exc}"}

def experiment_events(name:str, payload:Mapping)->dict:
    try:
        from mem20eventstreamsuperhighwayz.domain import create_stream,publish,throughput
        s=create_stream("sales-experiments"); publish(s,name,dict(payload)); tp=throughput(s)
        return {"ok":True,"subsystem":"mem20eventstreamsuperhighwayz","published":1,"throughput":tp}
    except Exception as exc: return {"ok":False,"subsystem":"mem20eventstreamsuperhighwayz","error":f"{type(exc).__name__}: {exc}"}

def deal_handoff(product:Mapping, customer:Mapping)->dict:
    try:
        from mem20autonomousdealdeskz.domain import approval_required, negotiate_round, price_deal
        price=price_deal(dict(product),dict(customer))
        needs=approval_required(price*customer.get("volume",1), threshold=10000)
        negotiated=negotiate_round(price, price*0.9, 2)
        return {"ok":True,"subsystem":"mem20autonomousdealdeskz","price":price,"approval_required":needs,"negotiated":negotiated}
    except Exception as exc: return {"ok":False,"subsystem":"mem20autonomousdealdeskz","error":f"{type(exc).__name__}: {exc}"}

def channel_routing(key:str, channels:Sequence[str])->dict:
    try:
        from mem20capabilitymarketplacez.domain import CapabilityMarketplace
        m=CapabilityMarketplace(replicas=32); caps=list(channels) or ["email","chat","phone"]
        for c in caps: m.add(c)
        owner=m.locate(key); dist=m.distribution(keys=100)
        return {"ok":True,"subsystem":"mem20capabilitymarketplacez","owner":owner,"channels":len(caps),"distribution_keys":sum(dist.values()) if hasattr(dist,'values') else 100}
    except Exception as exc: return {"ok":False,"subsystem":"mem20capabilitymarketplacez","error":f"{type(exc).__name__}: {exc}"}

def probe()->dict:
    checks={"content_outreach":content_outreach("hello"),"spam_guardrail":spam_guardrail(1.0,{"consent":True},True),"demand_timing":demand_timing([5,6,8,7]),"experiment_events":experiment_events("exp.run",{"id":"x"}),"deal_handoff":deal_handoff({"price":100},{"volume":10}),"channel_routing":channel_routing("lead-1",["email","chat"])}
    return {"ok":all(v.get("ok") for v in checks.values()),"checks":checks}
