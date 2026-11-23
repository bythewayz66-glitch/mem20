"""Self-optimizing kernel: tune params based on metrics, with estate report."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["optimize","score","search","kernel_health","kernel_report","probe","estate_context"]

def optimize(params, metrics, lr=0.1):
    new=dict(params)
    for k,v in metrics.items():
        if k in new: new[k]=new[k]+lr*(v-new[k])
    return new

def score(params, objective):
    return sum(params.get(k,0)*objective.get(k,0) for k in objective)

def search(params_space, objective, iterations=10, seed=0):
    rng=random.Random(seed); best=None; best_score=float("-inf")
    for _ in range(iterations):
        cand={k: rng.choice(v) for k,v in params_space.items()}
        s=score(cand,objective)
        if s>best_score: best_score=s; best=cand
    return {"params": best, "score": best_score}

def kernel_health(params):
    return {"params": len(params)}

def kernel_report():
    params={"a":1.0,"b":0.5}; metrics={"a":2.0}; tuned=optimize(params,metrics,0.5); sc=score(tuned,{"a":1,"b":1}); sr=search({"x":[1,2,3]},{"x":1},8,seed=1)
    peers={
        "causal_tuning": ecosystem.causal_tuning({"a":tuned.get("a",0)},{"a":1}),
        "demand_forecast": ecosystem.demand_forecast([1.0,1.2,1.4]),
        "counterfactual_eval": ecosystem.counterfactual_eval({"score":sc}),
        "tuning_events": ecosystem.tuning_events("kernel.optimized", {"score":sc,"best":sr["score"]}),
        "kernel_routing": ecosystem.kernel_routing("kernel", ["optimize","score","search"]),
        "tuning_containment": ecosystem.tuning_containment("search"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"tuned_a":tuned.get("a"),"score":sc,"search_score":sr["score"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=kernel_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
