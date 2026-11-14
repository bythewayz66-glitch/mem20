"""Offer genome engine: genetic optimization of offers (6 peers)."""
from __future__ import annotations
import random
from . import ecosystem
__all__=["create_genome","mutate","fitness","evolve","genome_report","probe","estate_context"]

def create_genome(offer):
    return {"offer": offer, "genes": {"price": offer.get("price", 0), "discount": 0.0, "bundle_size": len(offer.get("components", []))}, "fitness": 0.0}

def mutate(genome, rate=0.2, seed=0):
    rng = random.Random(seed)
    g = {"offer": genome["offer"], "genes": dict(genome["genes"]), "fitness": genome["fitness"]}
    for k in g["genes"]:
        if rng.random() < rate:
            if isinstance(g["genes"][k], (int, float)):
                g["genes"][k] = g["genes"][k] * (0.8 + rng.random()*0.4)
    return g

def fitness(genome, target_conversion=0.1):
    # higher discount -> higher conversion proxy
    conv = min(1.0, genome["genes"].get("discount", 0)*2 + 0.05)
    genome["fitness"] = round(conv, 4)
    return genome["fitness"]

def evolve(population, generations=5, seed=0):
    rng = random.Random(seed)
    pop = list(population)
    for _ in range(generations):
        for g in pop:
            fitness(g)
        pop.sort(key=lambda g: -g["fitness"])
        survivors = pop[:max(1, len(pop)//2)]
        pop = survivors + [mutate(g, seed=rng.randint(0,999)) for g in survivors]
    for g in pop:
        fitness(g)
    pop.sort(key=lambda g: -g["fitness"])
    return pop

def genome_report():
    pop=[create_genome({"price":10,"components":["a"]}) for _ in range(4)]
    ev=evolve(pop,generations=2,seed=1); fit=fitness(ev[0]) if ev else 0.0
    peers={
        "offer_fabric": ecosystem.offer_fabric(),
        "deal_desk": ecosystem.deal_desk(),
        "plg_sim": ecosystem.plg_sim(),
        "counterfactual": ecosystem.counterfactual(),
        "genome_events": ecosystem.genome_events("genome.evolved", {"fitness":fit}),
        "genome_routing": ecosystem.genome_routing("genome", ["mutate","fitness","evolve"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(ev)==4 and 0<=fit<=1,"population":len(ev),"fitness":fit,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20offergenomeenginez-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20offergenomeenginez-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=genome_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
