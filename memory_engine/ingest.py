"""Sensory / batch ingest -- first-class memory_engine capability.

Normalizes multi-modal inputs and writes grounded memories via remember().
Formerly mem20sensorymemoryingestz (in-memory stream + peer theater).
"""
from __future__ import annotations

import hashlib
import time
from typing import Any


def _normalize(content: Any, modality: str) -> str:
    if modality == "text":
        return str(content)
    if modality == "image":
        if isinstance(content, dict):
            return f"[image] {json_dumps_safe(content)}"
        return f"[image] {content}"
    if modality == "audio":
        return f"[audio] {content}"
    if modality == "sensor":
        if isinstance(content, dict):
            return f"[sensor] {json_dumps_safe(content)}"
        return f"[sensor] {content}"
    return f"[{modality}] {content}"


def json_dumps_safe(obj: Any) -> str:
    import json
    try:
        return json.dumps(obj, default=str)[:2000]
    except Exception:
        return str(obj)[:2000]


def ingest(
    content: Any,
    modality: str = "text",
    *,
    topic: str | None = None,
    tags: list[str] | None = None,
    persist: bool = True,
    epistemic_status: str = "observed",
) -> dict[str, Any]:
    """Ingest one sensory item into grounded memory.

    Returns the ledger row when persist=True, else a normalized preview.
    """
    mod = (modality or "text").lower().strip()
    text = _normalize(content, mod)
    t = topic or f"sensory:{mod}"
    tag_list = list(tags or []) + ["sensory", mod, "ingest"]
    entry = {
        "modality": mod,
        "topic": t,
        "content": text[:4000],
        "ts": time.time(),
        "content_hash": hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16],
    }
    if not persist:
        entry["persisted"] = False
        return entry
    try:
        from memory_engine import remember
        row = remember(
            topic=t,
            content=text[:4000],
            tags=tag_list,
            epistemic_status=epistemic_status,
        )
        if isinstance(row, dict):
            entry["id"] = row.get("id")
            entry["persisted"] = True
        else:
            entry["persisted"] = True
            entry["raw"] = row
    except Exception as exc:
        entry["persisted"] = False
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


def ingest_batch(
    items: list[dict[str, Any]],
    *,
    default_modality: str = "text",
    persist: bool = True,
) -> dict[str, Any]:
    """Ingest many items. Each item: {content, modality?, topic?, tags?}."""
    results = []
    ok = 0
    for it in items or []:
        r = ingest(
            it.get("content"),
            modality=it.get("modality") or default_modality,
            topic=it.get("topic"),
            tags=it.get("tags"),
            persist=persist,
        )
        results.append(r)
        if r.get("persisted"):
            ok += 1
    return {"total": len(results), "persisted": ok, "results": results}


def ingest_health() -> dict[str, Any]:
    try:
        from memory_engine import recall
        rows = recall(topic="sensory:", k=5, include_simulated=False) or []
        return {"ok": True, "recent_sensory": len(rows), "backend": "memory_engine.ledger"}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
