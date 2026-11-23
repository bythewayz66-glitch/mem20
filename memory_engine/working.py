"""Working memory — short-lived buffer that flushes to the grounded ledger.

Not a side package: the buffer is process-local; flush() writes via remember()
so durable state always lands on the same firewall path as the rest of the engine.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

_BUFFER: list[dict[str, Any]] = []
_MAX = 64


def _engine():
    from . import memory as eng
    return eng


def put(
    content: str,
    *,
    topic: str = "working",
    tags: list[str] | None = None,
    max_items: int = _MAX,
) -> dict[str, Any]:
    item = {
        "id": str(uuid.uuid4()),
        "content": content,
        "topic": topic,
        "tags": list(tags or []),
        "ts": time.time(),
    }
    _BUFFER.append(item)
    while len(_BUFFER) > max_items:
        _BUFFER.pop(0)
    return item


def get(item_id: str) -> dict[str, Any] | None:
    for it in _BUFFER:
        if it["id"] == item_id:
            return dict(it)
    return None


def list_working(*, topic: str | None = None, limit: int = 32) -> list[dict[str, Any]]:
    items = list(_BUFFER)
    if topic is not None:
        items = [i for i in items if i.get("topic") == topic]
    return items[-limit:]


def clear(topic: str | None = None) -> int:
    global _BUFFER
    if topic is None:
        n = len(_BUFFER)
        _BUFFER = []
        return n
    before = len(_BUFFER)
    _BUFFER = [i for i in _BUFFER if i.get("topic") != topic]
    return before - len(_BUFFER)


def flush(
    *,
    topic: str | None = None,
    epistemic_status: str = "observed",
    clear_after: bool = True,
) -> dict[str, Any]:
    """Write buffer items to the grounded ledger."""
    eng = _engine()
    items = list_working(topic=topic, limit=10_000)
    written = []
    for it in items:
        fact = eng.remember(
            topic=it.get("topic") or "working",
            content=it["content"],
            epistemic_status=epistemic_status,
            tags=["working_flush", *(it.get("tags") or [])],
        )
        fid = getattr(fact, "id", None) or (fact.get("id") if isinstance(fact, dict) else None)
        written.append({"working_id": it["id"], "fact_id": fid})
    if clear_after:
        clear(topic=topic)
    return {"flushed": len(written), "facts": written}


def working_health() -> dict[str, Any]:
    return {"ok": True, "module": "working", "buffered": len(_BUFFER), "max": _MAX}


__all__ = ["put", "get", "list_working", "clear", "flush", "working_health"]


# Preferred public names (avoid clashing with builtins)
working_put = put
working_get = get
working_clear = clear
working_flush = flush
