"""Planetary batch fabric: distributed batch jobs across regions (6 peers)."""
from __future__ import annotations
import time, uuid
from . import ecosystem
__all__=["submit_job","schedule","job_status","fabric_health","retry","fabric_report","probe","estate_context"]


def submit_job(region, payload, priority=0):
    return {"id": str(uuid.uuid4())[:8], "region": region, "payload": payload, "priority": priority, "status": "queued", "submitted": time.time()}


def schedule(jobs, capacity):
    # greedy by priority desc
    jobs = sorted(jobs, key=lambda j: -j.get("priority", 0))
    cap = dict(capacity)
    scheduled = []
    for j in jobs:
        if cap.get(j["region"], 0) > 0:
            cap[j["region"]] -= 1
            j["status"] = "scheduled"
            scheduled.append(j)
    return scheduled


def job_status(job):
    return job.get("status", "unknown")


def fabric_health(regions):
    return {"regions": len(regions), "capacity": sum(regions.values())}


def retry(job, max_retries=3):
    if job.get("retries", 0) < max_retries:
        job["retries"] = job.get("retries", 0) + 1
        job["status"] = "queued"
        return {"ok": True, "retries": job["retries"]}
    return {"ok": False, "reason": "max retries"}


def fabric_report():
    j=submit_job("us","p",1); sched=schedule([dict(j)],{"us":1}); h=fabric_health({"us":5,"eu":3}); rt=retry(submit_job("us","p",1))
    peers={
        "roaming_scheduler": ecosystem.roaming_scheduler(),
        "workcell_run": ecosystem.workcell_run(),
        "batch_events": ecosystem.batch_events("batch.scheduled", {"count":len(sched)}),
        "batch_routing": ecosystem.batch_routing("batch", ["submit","schedule","retry"]),
        "autonomous_recovery": ecosystem.autonomous_recovery(),
        "output_compile": ecosystem.output_compile(),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(sched)==1 and h["regions"]==2 and rt["ok"] is True,"scheduled":len(sched),"health":h,"peers":peers}


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
    ledger = DeliveryLedger(max_entries=4); ledger.add("mem20planetarybatchfabricz-work")
    ctx = {"path_scripts": len(mem20path.discover_scripts()), "inventory_keys": len(inventory) if isinstance(inventory, dict) else 0,
           "work_recorded": "mem20planetarybatchfabricz-work" in ledger, "focus_score": float(focus_score({"priority":1,"distractions":0})),
           "sitemap_skips_cache": is_skipped_dir("__pycache__")}
    if store_path is not None:
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=fabric_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
