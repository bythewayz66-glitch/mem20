"""Autonomous micro-SaaS foundry: idea scoring, MVP spec, launch plan, and estate report."""
from __future__ import annotations
from . import ecosystem

__all__=["score_idea","mvp_spec","launch_plan","revenue_projection","idea_ranking","foundry_report","probe","estate_context"]

def score_idea(idea):
    market=idea.get("market_size",0); competition=idea.get("competition",5); effort=idea.get("effort",5)
    score=(market/100.0)*(1/max(1,competition))*(1/max(1,effort))
    return round(min(1.0,score),4)

def mvp_spec(idea):
    return {"name":idea.get("name"),"core_features":idea.get("features",[])[:3],"tech_stack":idea.get("stack","python+react"),"timeline_weeks":max(2,idea.get("effort",4))}

def launch_plan(spec):
    return {"phases":["build","beta","launch","growth"],"beta_users":50,"launch_channels":["producthunt","twitter","reddit"],"pricing":spec.get("price",9)}

def revenue_projection(users, price, churn=0.05):
    mrr=users*price; annual=mrr*12*(1-churn)
    return {"mrr":mrr,"arr":round(annual,2)}

def idea_ranking(ideas):
    scored=[(score_idea(i),str((i or {}).get('name',(i or {}).get('id',''))),i) for i in ideas]; scored.sort(key=lambda x:(-x[0],x[1])); return [(sc,it) for sc,_n,it in scored]

def foundry_report(idea=None):
    idea = idea or {"name":"tool","market_size":800,"competition":2,"effort":3,"features":["auth","core","billing"],"price":9}
    spec=mvp_spec(idea); launch=launch_plan(spec); proj=revenue_projection(100, spec.get("pricing",9))
    peers={
        "economics": ecosystem.economics(100, float(spec.get("pricing",9))),
        "demand_signal": ecosystem.demand_signal([idea.get("market_size",100)/20.0]*5),
        "build_schedule": ecosystem.build_schedule(spec.get("core_features",[])),
        "launch_pipeline": ecosystem.launch_pipeline([{"deal_value":spec.get("pricing",9)*12,"budget":500,"authority":True,"need":True,"timeline_days":14,"touches":1}]),
        "content_quality": ecosystem.content_quality(f"launch {idea.get('name','saas')}"),
        "capability_routing": ecosystem.capability_routing(idea.get("name","foundry"), spec.get("core_features",["core"])),
    }
    return {"ok": all(v.get("ok") for v in peers.values()), "idea_score": score_idea(idea), "mvp_spec": spec, "launch_plan": launch, "revenue_projection": proj, "peers": peers}

def probe(): return ecosystem.probe()

def estate_context(store_path: str | None = None):
    _=store_path; r=foundry_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
