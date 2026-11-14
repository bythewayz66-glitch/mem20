"""Causal routing brain: causal inference for routing decisions, with estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["causal_effect","route_by_cause","confounder_adjust","intervention_value","causal_graph","routing_report","probe","estate_context"]

def causal_effect(treatment_outcomes, control_outcomes):
    if not treatment_outcomes or not control_outcomes: return 0.0
    return round(sum(treatment_outcomes)/len(treatment_outcomes)-sum(control_outcomes)/len(control_outcomes),4)

def route_by_cause(features, causal_weights):
    return float(round(sum(features.get(k,0)*w for k,w in causal_weights.items()),4))

def confounder_adjust(raw_effect, confounder_strength): return round(raw_effect*(1-confounder_strength),4)

def intervention_value(baseline, intervention_outcome): return round(intervention_outcome-baseline,4)

def causal_graph(edges):
    graph={}
    for src,dst in edges: graph.setdefault(src,[]).append(dst)
    return graph

def routing_report(features=None, weights=None, edges=None):
    features=features or {"latency":0.2,"error_rate":0.1,"load":0.3}; weights=weights or {"latency":-1.0,"error_rate":-2.0,"load":-0.5}; edges=edges or [("latency","route"),("error_rate","route")]
    score=route_by_cause(features,weights); g=causal_graph(edges); effect=causal_effect([1,1,0],[0,0,1])
    peers={
        "counterfactual_route": ecosystem.counterfactual_route({"latency":features.get("latency",0)}, {"effect":0.1}),
        "route_events": ecosystem.route_events("causal.route", {"score":score}),
        "capability_target": ecosystem.capability_target(str(score), ["low-latency","reliable"]),
        "failure_signal": ecosystem.failure_signal("router"),
        "health_signal": ecosystem.health_signal(["router","target"]),
        "node_targets": ecosystem.node_targets({"capability":"cpu"}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"route_score":score,"causal_effect_sample":effect,"graph_nodes":len(g),"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=routing_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
