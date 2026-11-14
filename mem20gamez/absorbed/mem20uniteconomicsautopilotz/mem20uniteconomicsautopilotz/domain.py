"""Unit economics autopilot with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["ltv","cac","payback_months","ltv_cac_ratio","economics_health","economics_report","probe","estate_context"]

def ltv(arpu, churn_rate, months=12):
    if churn_rate <= 0: return arpu*months
    return round(arpu/churn_rate, 4) if churn_rate else arpu*months
def cac(spend, customers): return round(spend/customers,4) if customers else 0.0
def payback_months(cac_val, arpu): return round(cac_val/arpu,4) if arpu else 0.0
def ltv_cac_ratio(ltv_val, cac_val): return round(ltv_val/cac_val,4) if cac_val else 0.0
def economics_health(metrics): return dict(metrics)

def economics_report():
    l=ltv(10,0.1); c=cac(100,5); pb=payback_months(c,10); r=ltv_cac_ratio(l,c); h=economics_health({"ltv":l,"cac":c,"ratio":r})
    peers={
        "revenue_check": ecosystem.revenue_check(),
        "plg_sim": ecosystem.plg_sim(),
        "business_model": ecosystem.business_model(),
        "economics_events": ecosystem.economics_events("economics.report", {"ratio":r}),
        "economics_routing": ecosystem.economics_routing("economics", ["ltv","cac","payback"]),
        "economics_health_peer": ecosystem.economics_health_peer(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and r==5.0,"ltv":l,"cac":c,"payback":pb,"ratio":r,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20uniteconomicsautopilotz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20uniteconomicsautopilotz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=economics_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
