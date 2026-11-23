"""Consolidation helpers on the grounded ledger (prune / merge / promote).

Wraps existing engine primitives so agents have one place for memory hygiene
instead of hunting package stubs.
"""
from __future__ import annotations

from typing import Any


def _engine():
    from . import memory as eng
    return eng


def prune_superseded() -> dict[str, Any]:
    eng = _engine()
    if hasattr(eng, "prune"):
        result = eng.prune()
        if isinstance(result, dict):
            return {"ok": True, **result}
        return {"ok": True, "result": result}
    return {"ok": False, "error": "prune_not_available"}


def consolidate_topic(topic: str, *, keep: int = 5, epistemic_status: str = "observed") -> dict[str, Any]:
    """Keep the newest ``keep`` facts for a topic; supersede older noise as a summary."""
    eng = _engine()
    try:
        facts = eng.recall(topic=topic, k=max(keep * 4, 20))
    if len(facts) <= keep:
        return {"ok": True, "topic": topic, "kept": len(facts), "summarized": 0}
    # facts assumed newest-first; keep head, summarize tail
    keep_facts = facts[:keep]
    old = facts[keep:]
    lines = []
    for f in old:
        c = f.content if hasattr(f, "content") else f.get("content", "")
        lines.append(str(c)[:200])
    summary = f"[consolidated {len(old)} older facts] " + " | ".join(lines)[:1500]
    eng.remember(
        topic=topic,
        content=summary,
        epistemic_status=epistemic_status,
        tags=["consolidated"],
    )
    return {"ok": True, "topic": topic, "kept": len(keep_facts), "summarized": len(old)}


def promote_all_due_simulated() -> dict[str, Any]:
    eng = _engine()
    if hasattr(eng, "promote_simulated_to_grounded") and hasattr(eng, "list_simulated"):
        listed = eng.list_simulated()
        ids = []
        if isinstance(listed, list):
            for x in listed:
                i = getattr(x, "id", None) or (x.get("id") if isinstance(x, dict) else None)
                if i:
                    ids.append(i)
        promoted = 0
        for i in ids[:50]:
            try:
                eng.promote_simulated_to_grounded(i)
                promoted += 1
            except Exception:
                pass
        return {"ok": True, "promoted": promoted, "candidates": len(ids)}
    return {"ok": False, "error": "promote_path_unavailable"}


def consolidate_health() -> dict[str, Any]:
    eng = _engine()
    try:
        h = eng.status() if hasattr(eng, "status") else {}
    except Exception as e:
        h = {"error": str(e)}
    return {"ok": True, "module": "consolidate", "engine_status": h if isinstance(h, dict) else str(h)}


__all__ = [
    "prune_superseded", "consolidate_topic", "promote_all_due_simulated", "consolidate_health",
]
