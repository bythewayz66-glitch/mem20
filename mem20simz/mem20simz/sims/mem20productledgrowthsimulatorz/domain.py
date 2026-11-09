"""Product-led growth simulator: funnels, virality, retention, with estate report."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["funnel","viral_coefficient","retention_curve","growth_score","simulate","plg_report","probe","estate_context"]

def funnel(users, stages):
    counts=[users]
    for s in stages:
        rate=s.get("conversion",0.5); counts.append(int(counts[-1]*rate))
    return counts

def viral_coefficient(invites_per_user, conversion_rate):
    return round(invites_per_user * conversion_rate, 4)

def retention_curve(users, churn_rate, periods=6):
    out=[users]
    for _ in range(periods): out.append(int(out[-1]*(1-churn_rate)))
    return out

def growth_score(metrics):
    k=metrics.get("viral_k",0); conv=metrics.get("conversion",0); ret=metrics.get("retention",0)
    return round((k+conv+ret)/3, 4)

def simulate(params, seed=0):
    rng=random.Random(seed); _=rng
    users=params.get("starting_users",100)
    k=viral_coefficient(params.get("invites",2), params.get("invite_conv",0.1))
    growth=users*(1+k)
    return {"starting": users, "viral_k": k, "after_viral": int(growth)}

def plg_report(params=None):
    params=params or {"starting_users":100,"invites":2,"invite_conv":0.1}
    sim=simulate(params,seed=1); f=funnel(100,[{"conversion":0.5},{"conversion":0.4}]); ret=retention_curve(100,0.1,3); score=growth_score({"viral_k":sim["viral_k"],"conversion":0.4,"retention":0.8})
    peers={
        "business_economics": ecosystem.business_economics(sim["after_viral"],10.0),
        "lifecycle_retention": ecosystem.lifecycle_retention(),
        "pipeline_conversion": ecosystem.pipeline_conversion(),
        "loyalty_expansion": ecosystem.loyalty_expansion(),
        "growth_forecast": ecosystem.growth_forecast([100,sim["after_viral"],sim["after_viral"]*1.1]),
        "funnel_events": ecosystem.funnel_events("plg.report", {"viral_k":sim["viral_k"],"score":score}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"viral_k":sim["viral_k"],"funnel":f,"growth_score":score,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=plg_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
