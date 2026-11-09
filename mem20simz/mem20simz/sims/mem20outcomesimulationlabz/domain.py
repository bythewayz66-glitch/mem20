"""Outcome simulation lab: Monte Carlo, scenarios, risk (6 peers)."""
from __future__ import annotations
import random, statistics
from . import ecosystem
__all__=["simulate_once","monte_carlo","summarize","scenario_compare","risk_of_loss","simulation_report","probe","estate_context"]

def simulate_once(params, seed=0):
    rng = random.Random(seed)
    base = params.get("base", 100)
    noise = rng.gauss(0, params.get("std", 10))
    return base + noise

def monte_carlo(params, n=100, seed=0):
    rng = random.Random(seed)
    results = []
    for i in range(n):
        results.append(simulate_once(params, seed=rng.randint(0, 10**6)))
    return results

def summarize(results):
    return {"mean": round(statistics.mean(results),4), "std": round(statistics.pstdev(results),4),
            "min": round(min(results),4), "max": round(max(results),4), "p5": round(sorted(results)[int(len(results)*0.05)],4)}

def scenario_compare(scenarios):
    out = []
    for s in scenarios:
        res = monte_carlo(s["params"], n=50, seed=s.get("seed",0))
        out.append({"name": s["name"], **summarize(res)})
    return out

def risk_of_loss(results, threshold=0):
    return sum(1 for r in results if r < threshold) / max(1, len(results))

def simulation_report():
    res=monte_carlo({"base":100,"std":5},n=20,seed=1); summ=summarize(res)
    peers={
        "counterfactual": ecosystem.counterfactual(),
        "business_twin": ecosystem.business_twin(),
        "business_model": ecosystem.business_model(),
        "sim_events": ecosystem.sim_events("sim.run", {"mean":summ["mean"]}),
        "sim_routing": ecosystem.sim_routing("sim", ["simulate","summarize","compare"]),
        "causal_routing": ecosystem.causal_routing({"signal":1},{"signal":1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(res)==20 and "mean" in summ,"runs":len(res),"summary":summ,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20simz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20simz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=simulation_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
