"""Personal cognitive search -- first-class memory_engine capability.

Ranked search across grounded memory. Formerly mem20personalcognitivesearchz.
"""
from __future__ import annotations

from typing import Any


def cognitive_search(
    query: str,
    *,
    k: int = 10,
    topic: str | None = None,
    include_simulated: bool = False,
    mode: str = "hybrid",
) -> list[dict[str, Any]]:
    """Search memory. mode: hybrid | semantic | keyword."""
    q = (query or "").strip()
    if not q:
        return []
    results: list[dict[str, Any]] = []
    if mode in ("hybrid", "semantic"):
        try:
            from memory_engine import recall_hybrid
            rows = recall_hybrid(q, k=k, topic=topic) if mode == "hybrid" else None
            if rows is None:
                from memory_engine import recall_semantic
                rows = recall_semantic(q, k=k, topic=topic)
            for r in rows or []:
                if isinstance(r, dict):
                    results.append({**r, "_source": mode})
                else:
                    results.append({"content": str(r), "_source": mode})
        except Exception:
            pass
    if mode == "keyword" or not results:
        try:
            from memory_engine import recall
            rows = recall(topic=topic or q, k=k, include_simulated=include_simulated) or []
            tokens = set(q.lower().split())
            scored = []
            for r in rows:
                text = f"{r.get('topic','')} {r.get('content','')}".lower()
                score = sum(1 for t in tokens if t in text)
                scored.append((score, r))
            scored.sort(key=lambda x: -x[0])
            for score, r in scored[:k]:
                results.append({**r, "_score": score, "_source": "keyword"})
        except Exception:
            pass
    seen = set()
    out = []
    for r in results:
        rid = r.get("id") or r.get("content")
        if rid in seen:
            continue
        seen.add(rid)
        out.append(r)
    return out[:k]


def search_health() -> dict[str, Any]:
    try:
        from memory_engine import index_health
        h = index_health()
        return {"ok": True, "index_health": h if isinstance(h, dict) else str(h)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
