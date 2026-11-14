"""Cross-product loyalty graph: edges, centrality, recommendations, with estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["add_edge","degree","centrality","recommend_products","loyalty_score","loyalty_report","probe","estate_context"]

def add_edge(graph, a, b, weight=1.0):
    graph.setdefault(a, {}).setdefault(b, 0.0); graph.setdefault(b, {}).setdefault(a, 0.0)
    graph[a][b] += weight; graph[b][a] += weight
    return graph

def degree(graph, node): return len(graph.get(node, {}))

def centrality(graph):
    if not graph: return {}
    mx = max((degree(graph,n) for n in graph), default=1) or 1
    return {n: round(degree(graph,n)/mx, 4) for n in graph}

def recommend_products(graph, user_products, top=3):
    scores={}
    for p in user_products:
        for neighbor,w in graph.get(p,{}).items():
            if neighbor not in user_products: scores[neighbor]=scores.get(neighbor,0.0)+w
    ranked=sorted(scores.items(), key=lambda x: -x[1])
    return [{"product":k,"score":round(v,4)} for k,v in ranked[:top]]

def loyalty_score(user_products, graph):
    if not user_products or not graph: return 0.0
    total=0.0
    for p in user_products: total += sum(graph.get(p,{}).values())
    return round(total/max(1,len(user_products)),4)

def loyalty_report(graph=None, user_products=None):
    graph = graph or {}
    if not graph:
        add_edge(graph,"core","addon",1.0); add_edge(graph,"core","pro",0.8); add_edge(graph,"addon","pro",0.5)
    user_products = user_products or ["core"]
    cent=centrality(graph); rec=recommend_products(graph,user_products,2); score=loyalty_score(user_products,graph)
    peers={
        "lifecycle_value": ecosystem.lifecycle_value(),
        "business_value": ecosystem.business_value(20,25.0),
        "pipeline_signal": ecosystem.pipeline_signal(),
        "challenge_engagement": ecosystem.challenge_engagement(),
        "loyalty_events": ecosystem.loyalty_events("loyalty.report", {"score":score,"recommendations":len(rec)}),
        "capability_routing": ecosystem.capability_routing("loyalty", ["recommend","upsell"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"loyalty_score":score,"recommendations":rec,"centrality":cent,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=loyalty_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
