"""Style guide agent with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["check","fix","style_score","style_health","style_report","probe","estate_context"]

def check(content, rules):
    issues=[]
    for r in rules or []:
        if r.get("type")=="max_length" and len(content)>r.get("value",9999):
            issues.append({"type":"max_length","actual":len(content)})
    return issues
def fix(content, issues): return content
def style_score(content, rules): issues=check(content,rules); return 1.0 if not issues else max(0.0,1.0-len(issues)*0.2)
def style_health(content, rules): return {"score":style_score(content,rules),"issues":len(check(content,rules))}

def style_report():
    rules=[{"type":"max_length","value":20}]; h=style_health("hi", rules)
    peers={
        "output_compile": ecosystem.output_compile(),
        "software_foundry": ecosystem.software_foundry(),
        "context_compression": ecosystem.context_compression("style guide text"),
        "style_events": ecosystem.style_events("style.checked", {"score":h["score"]}),
        "style_routing": ecosystem.style_routing("style", ["check","fix","score"]),
        "style_health_peer": ecosystem.style_health_peer(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["score"]==1.0,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20styleguideagentz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20styleguideagentz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=style_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
