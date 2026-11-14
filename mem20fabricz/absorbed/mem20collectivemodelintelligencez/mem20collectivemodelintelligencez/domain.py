"""Collective model intelligence: ensemble, voting, aggregation, with estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["ensemble_predict","diversity_score","knowledge_distill","aggregate_confidence","collective_report","probe","estate_context"]

def ensemble_predict(predictions, weights=None):
    if not predictions: return None
    if weights is None: weights=[1.0]*len(predictions)
    total_w=sum(weights)
    if total_w==0: return None
    if isinstance(predictions[0], (int,float)): return round(sum(p*w for p,w in zip(predictions,weights))/total_w,4)
    votes={}
    for p,w in zip(predictions,weights): votes[p]=votes.get(p,0)+w
    return max(votes, key=votes.get)

def diversity_score(models_predictions):
    if len(models_predictions)<2: return 0.0
    disagreements=0; total=0
    for i in range(len(models_predictions)):
        for j in range(i+1,len(models_predictions)):
            total+=1
            if models_predictions[i]!=models_predictions[j]: disagreements+=1
    return round(disagreements/max(1,total),4)

def knowledge_distill(teacher_preds, student_preds, temperature=2.0):
    _=temperature; loss=sum((t-s)**2 for t,s in zip(teacher_preds,student_preds))
    return round(loss/max(1,len(teacher_preds)),4)

def aggregate_confidence(confidences):
    if not confidences: return 0.0
    return round(sum(confidences)/len(confidences),4)

def collective_report(predictions=None, confidences=None):
    predictions=predictions or [0.8,0.7,0.9]; confidences=confidences or [0.9,0.8,0.85]
    ens=ensemble_predict(predictions); div=diversity_score(predictions); conf=aggregate_confidence(confidences)
    peers={
        "model_fusion": ecosystem.model_fusion([{"id":"a","accuracy":0.8,"confidence":confidences[0],"prediction":"yes"},{"id":"b","accuracy":0.7,"confidence":confidences[1],"prediction":"no"}]),
        "generation_quality": ecosystem.generation_quality("collective model summary"),
        "model_routing": ecosystem.model_routing("ensemble-1",["inference","embed"]),
        "ensemble_events": ecosystem.ensemble_events("collective.report",{"ensemble":ens,"confidence":conf}),
        "model_health": ecosystem.model_health(["model-a","model-b"]),
        "causal_route": ecosystem.causal_route({"quality":conf,"diversity":div},{"quality":1.0,"diversity":0.5}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"ensemble":ens,"diversity":div,"confidence":conf,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=collective_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
