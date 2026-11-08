"""Opportunity radar: scan signals, score, alert (6 peers)."""
from __future__ import annotations
import math, time
from . import ecosystem
__all__=["scan","score_opportunity","rank","alert","radar_health","radar_report","probe","estate_context"]

def scan(signals, threshold=0.5):
    return [s for s in signals if s.get("score", 0) >= threshold]

def score_opportunity(opp, context):
    base = opp.get("value", 0) * opp.get("probability", 0.5)
    urgency = context.get("urgency", 1.0)
    return round(base * urgency, 4)

def rank(opps, context):
    scored = [(score_opportunity(o, context), o) for o in opps]
    scored.sort(reverse=True)
    return [o for _, o in scored]

def alert(opps, threshold=0.7):
    return [o for o in opps if o.get("score", 0) >= threshold]

def radar_health(opps):
    return {"total": len(opps), "high": sum(1 for o in opps if o.get("score",0)>=0.7)}

def radar_report():
    scanned=scan([{"score":0.3},{"score":0.8}],0.5); h=radar_health([{"score":0.8}])
    peers={
        "sales_lab": ecosystem.sales_lab(),
        "plg_sim": ecosystem.plg_sim(),
        "causal_routing": ecosystem.causal_routing({"urgency":1},{"urgency":1}),
        "revenue_check": ecosystem.revenue_check(),
        "radar_events": ecosystem.radar_events("radar.alert", {"high":h["high"]}),
        "radar_routing": ecosystem.radar_routing("radar", ["scan","score","alert"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(scanned)==1 and h["high"]==1,"scanned":len(scanned),"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20opportunityradarz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20opportunityradarz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=radar_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
