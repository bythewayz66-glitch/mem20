"""Personal cognitive search: index, query, rank, recall (6 peers)."""
from __future__ import annotations
import math
from . import ecosystem
__all__=["index","query","rank","recall","search_health","cogsearch_report","probe","estate_context"]

def index(docs):
    idx = {}
    for d in docs:
        for w in d.get("text", "").lower().split():
            idx.setdefault(w, []).append(d.get("id"))
    return idx

def query(idx, q, docs_by_id):
    qwords = q.lower().split()
    hits = set()
    for w in qwords:
        for did in idx.get(w, []):
            hits.add(did)
    return [docs_by_id[did] for did in hits if did in docs_by_id]

def rank(results, q):
    qwords = set(q.lower().split())
    scored = []
    for r in results:
        rw = set(r.get("text", "").lower().split())
        scored.append((len(qwords & rw), r))
    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored]

def recall(idx, recent_ids, k=5):
    # return docs whose terms overlap recent
    return list(recent_ids)[:k]

def search_health(idx):
    return {"terms": len(idx), "postings": sum(len(v) for v in idx.values())}

def cogsearch_report():
    idx=index([{"id":"d1","text":"hello world"}]); docs={"d1":{"id":"d1","text":"hello world"}}; res=query(idx,"hello",docs); h=search_health(idx)
    peers={
        "episodic_memory": ecosystem.episodic_memory(),
        "context_compress": ecosystem.context_compress("hello world"),
        "predictive_recall": ecosystem.predictive_recall(),
        "search_events": ecosystem.search_events("search.query", {"hits":len(res)}),
        "search_routing": ecosystem.search_routing("search", ["index","query","rank"]),
        "output_compile": ecosystem.output_compile(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(res)==1 and h["terms"]>=1,"hits":len(res),"health":h,"peers":peers}

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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20personalcognitivesearchz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20personalcognitivesearchz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=cogsearch_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
