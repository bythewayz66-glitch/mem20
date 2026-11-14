"""Synthetic evaluator arena with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["create_arena","evaluate","leaderboard","arena_health","arena_report","probe","estate_context"]

def create_arena(agents): return {"agents":list(agents),"evaluations":[]}
def evaluate(arena, evaluator, subject, score): arena.setdefault("evaluations",[]).append({"evaluator":evaluator,"subject":subject,"score":score}); return arena
def leaderboard(arena):
    scores={}
    for e in arena.get("evaluations",[]): scores[e["subject"]]=scores.get(e["subject"],[])+[e["score"]]
    lb=[{"agent":a,"avg":sum(v)/len(v)} for a,v in scores.items()]
    return sorted(lb,key=lambda x:-x["avg"])
def arena_health(arena): return {"agents":len(arena.get("agents",[])),"evaluations":len(arena.get("evaluations",[]))}

def arena_report():
    a=create_arena(["a","b"]); evaluate(a,"a","b",0.9); h=arena_health(a); lb=leaderboard(a)
    peers={
        "collective_intel": ecosystem.collective_intel(),
        "counterfactual_eval": ecosystem.counterfactual_eval(),
        "output_compile": ecosystem.output_compile(),
        "arena_events": ecosystem.arena_events("arena.eval", {"evals":h["evaluations"]}),
        "arena_routing": ecosystem.arena_routing("arena", ["create","eval","rank"]),
        "arena_containment": ecosystem.arena_containment("eval"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["evaluations"]==1,"health":h,"leaderboard":lb,"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None):
    from pathlib import Path
    import mem20path
    from memory_engine import EngineConfig, MemoryEngine
    from mem20mixedinitiativefocusenginez.domain import focus_score
    from mem20sitemapz.policy import is_skipped_dir
    from mem20webhooksupernetworkz.domain import DeliveryLedger
    from toolchest.catalog import load_inventory
    root = Path(__file__).resolve().parents[2]
    inventory_path = root / "toolchest" / "inventory.json"
    if not inventory_path.exists(): inventory_path = root / "toolchest" / "src" / "toolchest" / "inventory.json"
    inventory = load_inventory(inventory_path)
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20syntheticevaluatorarenaz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20syntheticevaluatorarenaz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=arena_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
