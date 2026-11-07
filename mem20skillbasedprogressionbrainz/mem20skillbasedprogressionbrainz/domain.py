"""Skill-based progression brain with 6 peers."""
from __future__ import annotations
from . import ecosystem
__all__=["gain_xp","unlock_skill","level","progression_health","progression_report","probe","estate_context"]

def gain_xp(player, amount):
    player["xp"]=player.get("xp",0)+amount; player.setdefault("skills",[]); player["level"]=level(player); return player

def unlock_skill(player, skill, cost):
    if player.get("xp",0) < cost: return {"ok":False,"reason":"xp"}
    player["xp"]-=cost; player.setdefault("skills",[]).append(skill); return {"ok":True,"skill":skill}

def level(player):
    return 1 + player.get("xp",0)//100

def progression_health(player):
    return {"level":level(player),"xp":player.get("xp",0),"skills":len(player.get("skills",[]))}

def progression_report():
    p=gain_xp({"xp":0},120); unlock_skill(p,"s1",20); h=progression_health(p)
    peers={
        "skill_graph": ecosystem.skill_graph(),
        "motivation_twin": ecosystem.motivation_twin(),
        "reward_forge": ecosystem.reward_forge(),
        "progression_events": ecosystem.progression_events("progression.unlock", {"level":h["level"]}),
        "progression_routing": ecosystem.progression_routing("player", ["xp","unlock","level"]),
        "progression_health_peer": ecosystem.progression_health_peer(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["level"]>=2,"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20skillbasedprogressionbrainz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20skillbasedprogressionbrainz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=progression_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
