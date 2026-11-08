"""Domain for mem20pipelinez crew runtime (6 peers)."""
from __future__ import annotations
from . import ecosystem
from . import MEMBERS, __version__
__all__=["MEMBERS","__version__","pipeline_report","probe","estate_context"]


def pipeline_report():
    peers={
        "automation_canvas": ecosystem.automation_canvas(),
        "workcell_run": ecosystem.workcell_run(),
        "output_compile": ecosystem.output_compile(),
        "pipeline_events": ecosystem.pipeline_events("pipeline.status", {"members":len(MEMBERS)}),
        "pipeline_routing": ecosystem.pipeline_routing("pipeline", ["stage","build","validate"]),
        "causal_routing": ecosystem.causal_routing({"stage":1},{"stage":1}),
    }
    return {"ok":all(v.get("ok") for v in peers.values()) and len(MEMBERS)==12,"version":__version__,"members":list(MEMBERS),"member_count":len(MEMBERS),"peers":peers}


def probe(): return ecosystem.probe()


def estate_context(store_path=None):
    # Superset: legacy-style live estate fields + peer context
    from pathlib import Path
    ctx={"version":__version__,"members":list(MEMBERS),"member_count":len(MEMBERS),"engine_status_checked":False}
    if store_path is not None:
        from memory_engine import EngineConfig, MemoryEngine
        config = EngineConfig(store_path=Path(store_path).expanduser().resolve()); MemoryEngine(config); ctx["engine_status_checked"]=True
    r=pipeline_report(); ctx["peer_count"]=len(r.get("peers",{})); ctx["peers_ok"]=r.get("ok"); ctx["checks"]=r.get("peers",{})
    return ctx
