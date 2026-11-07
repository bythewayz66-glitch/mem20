"""Spatial command universe with 6 peers."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["create_region","add_entity","distance","in_region","spatial_health","spatial_report","probe","estate_context"]

def create_region(name, bounds): return {"name":name,"bounds":bounds,"entities":[]}
def add_entity(region, entity, pos): region.setdefault("entities",[]).append({"entity":entity,"pos":tuple(pos)}); return region
def distance(a, b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def in_region(region, pos):
    b=region.get("bounds") or []
    if len(b)<2: return False
    (xmin,xmax),(ymin,ymax)=b[0],b[1]
    return xmin<=pos[0]<=xmax and ymin<=pos[1]<=ymax
def spatial_health(regions): return {"regions":len(regions),"entities":sum(len(r.get("entities",[])) for r in regions)}

def spatial_report():
    r=create_region("r1",[(0,10),(0,10)]); add_entity(r,"e1",(5,5)); h=spatial_health([r]); d=distance((0,0),(3,4))
    peers={
        "workcell_dispatch": ecosystem.workcell_dispatch(),
        "causal_routing": ecosystem.causal_routing({"entities":h["entities"]},{"entities":1}),
        "spatial_events": ecosystem.spatial_events("spatial.command", {"regions":h["regions"]}),
        "spatial_routing": ecosystem.spatial_routing("region-r1", ["move","query","command"]),
        "spatial_containment": ecosystem.spatial_containment("command"),
        "spatial_health_peer": ecosystem.spatial_health_peer(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and h["entities"]==1 and d==5.0,"health":h,"distance":d,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20spatialcommanduniversez-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20spatialcommanduniversez-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    else: ctx["engine_status_checked"]=False
    r=spatial_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{}); return ctx
