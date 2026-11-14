"""Skill memory transfer with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["extract","transfer","merge_skills","transfer_health","transfer_report","probe","estate_context"]

def extract(agent, skill): return (agent.get("skills") or {}).get(skill)
def transfer(src, dst, skill):
    s=extract(src,skill)
    if s is None: return {"ok":False,"reason":"missing"}
    dst.setdefault("skills",{})[skill]=s; return {"ok":True,"skill":skill}
def merge_skills(agent, incoming): agent.setdefault("skills",{}).update(incoming or {}); return agent
def transfer_health(transfers): ok=sum(1 for t in transfers if t.get("ok")); return {"ok":ok,"fail":len(transfers)-ok,"total":len(transfers)}

def transfer_report():
    src={"skills":{"s1":{"w":1}}}; dst={}; t1=transfer(src,dst,"s1"); t2=transfer(src,dst,"missing"); h=transfer_health([t1,t2])
    peers={
        "skill_graph": ecosystem.skill_graph(),
        "episodic_memory": ecosystem.episodic_memory(),
        "memory_timemachine": ecosystem.memory_timemachine(),
        "transfer_events": ecosystem.transfer_events("transfer.done", {"ok":h["ok"]}),
        "transfer_routing": ecosystem.transfer_routing("agent", ["extract","transfer","merge"]),
        "transfer_containment": ecosystem.transfer_containment("transfer"),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["ok"]==1,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20skillmemorytransferz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20skillmemorytransferz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=transfer_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
