"""Runtime prompt optimizer: optimize prompts for cost/quality, with estate report."""
from __future__ import annotations
import re
from . import ecosystem
__all__=["tokenize","compress","score_prompt","optimize","prompt_health","prompt_report","probe","estate_context"]

def tokenize(prompt): return prompt.split()

def compress(prompt, max_tokens=100):
    toks=tokenize(prompt)
    if len(toks)<=max_tokens: return prompt
    return " ".join(toks[:max_tokens]) + "..."

def score_prompt(prompt, metrics):
    score=0.0
    for k,w in metrics.items():
        if k.lower() in prompt.lower(): score += w
    return round(score, 4)

def optimize(prompt, metrics, max_tokens=100):
    compressed=compress(prompt, max_tokens)
    return {"prompt": compressed, "score": score_prompt(compressed, metrics), "tokens": len(tokenize(compressed))}

def prompt_health(prompts):
    return {"count": len(prompts), "avg_tokens": round(sum(len(tokenize(p)) for p in prompts)/max(1,len(prompts)),2)}

def prompt_report():
    prompt="write a clear and helpful answer with good structure and examples"
    metrics={"clear":1.0,"helpful":1.0,"structure":0.5}
    opt=optimize(prompt, metrics, max_tokens=50)
    peers={
        "context_compression": ecosystem.context_compression(prompt),
        "causal_routing": ecosystem.causal_routing({"tokens":opt["tokens"]},{"tokens":0.1}),
        "capability_routing": ecosystem.capability_routing("prompt", ["tokenize","compress","score","optimize"]),
        "prompt_events": ecosystem.prompt_events("prompt.optimized", {"score":opt["score"],"tokens":opt["tokens"]}),
        "optimize_containment": ecosystem.optimize_containment("p1"),
        "cost_forecast": ecosystem.cost_forecast([opt["tokens"], opt["tokens"]*0.9, opt["tokens"]*0.8]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and opt["score"]>0,"score":opt["score"],"tokens":opt["tokens"],"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=prompt_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
