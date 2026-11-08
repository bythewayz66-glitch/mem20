"""Personal model evolution: user-specific model adaptation (6 peers)."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["create_model","adapt","predict","reset","evolution_health","evolution_report","probe","estate_context"]

def create_model(user, base="base"):
    return {"user": user, "base": base, "weights": {}, "version": 1, "interactions": 0}

def adapt(model, feedback, lr=0.1):
    model["interactions"] += 1
    for k, v in feedback.items():
        cur = model["weights"].get(k, 0.0)
        model["weights"][k] = cur + lr * (v - cur)
    model["version"] += 1
    return model

def predict(model, features):
    score = 0.0
    for k, v in features.items():
        score += model["weights"].get(k, 0.0) * v
    return score

def reset(model):
    model["weights"] = {}
    model["version"] = 1
    model["interactions"] = 0
    return model

def evolution_health(model):
    return {"version": model["version"], "interactions": model["interactions"], "weights": len(model["weights"])}

def evolution_report():
    m=create_model("u1"); adapt(m,{"x":1.0}); h=evolution_health(m); pred=predict(m,{"x":1})
    peers={
        "collective_intel": ecosystem.collective_intel(),
        "skill_transfer": ecosystem.skill_transfer(),
        "episodic_memory": ecosystem.episodic_memory(),
        "evo_events": ecosystem.evo_events("model.adapted", {"version":h["version"]}),
        "evo_routing": ecosystem.evo_routing("evo", ["adapt","predict","reset"]),
        "causal_routing": ecosystem.causal_routing({"signal":1},{"signal":1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["version"]==2,"health":h,"prediction":pred,"peers":peers}

def probe(): return ecosystem.probe()

def estate_context(store_path=None):
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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20personalmodelevolutionz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20personalmodelevolutionz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=evolution_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
