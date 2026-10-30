"""Ebbinghaus forgetting curve with spaced reinforcement scheduling."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any


def retention(elapsed_days: float, stability_days: float) -> float:
    if stability_days <= 0:
        return 0.0
    return math.exp(-max(0.0, float(elapsed_days)) / float(stability_days))


def reinforce(stability_days: float, *, success: bool = True, growth: float = 1.8, decay: float = 0.4) -> float:
    s = max(1e-6, float(stability_days))
    return s * (growth if success else decay)


def review_state(last_review_ts: float, stability_days: float, now_ts: float | None = None, threshold: float = 0.5) -> dict[str, Any]:
    now_ts = time.time() if now_ts is None else now_ts
    elapsed = (now_ts - last_review_ts) / 86400.0
    r = retention(elapsed, stability_days)
    next_days = round(-math.log(threshold) * stability_days, 4) if threshold > 0 else None
    return {
        "elapsed_days": round(elapsed, 4),
        "stability_days": round(float(stability_days), 4),
        "retention": round(r, 6),
        "retrievable": bool(r >= threshold - 1e-9),
        "threshold": threshold,
        "next_review_days": next_days,
    }


def review_queue(items: list[dict[str, Any]], now_ts: float | None = None, threshold: float = 0.5, limit: int = 20) -> dict[str, Any]:
    now_ts = time.time() if now_ts is None else now_ts
    scored = []
    for it in items:
        st = review_state(it["last_review_ts"], it.get("stability_days", 1.0), now_ts, threshold)
        st["id"] = it.get("id")
        scored.append(st)
    scored.sort(key=lambda s: s["retention"])
    due = [s for s in scored if not s["retrievable"]]
    return {"due_count": len(due), "queue": due[:limit], "scheduled": len(scored) - len(due)}


@dataclass
class MemoryItem:
    id: str
    last_review_ts: float
    stability_days: float = 1.0
    content: str = ""
    tags: list[str] = field(default_factory=list)

    def state(self, now_ts: float | None = None, threshold: float = 0.5) -> dict[str, Any]:
        return review_state(self.last_review_ts, self.stability_days, now_ts, threshold)

    def review(self, success: bool = True, now_ts: float | None = None) -> None:
        now_ts = time.time() if now_ts is None else now_ts
        self.stability_days = reinforce(self.stability_days, success=success)
        self.last_review_ts = now_ts


class ForgettingEngine:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self._items: dict[str, MemoryItem] = {}

    def add(self, item_id: str, content: str = "", stability_days: float = 1.0, tags: list[str] | None = None) -> MemoryItem:
        item = MemoryItem(id=item_id, last_review_ts=time.time(), stability_days=stability_days, content=content, tags=list(tags or []))
        self._items[item_id] = item
        return item

    def review(self, item_id: str, success: bool = True) -> dict[str, Any]:
        item = self._items[item_id]
        item.review(success=success)
        return item.state(threshold=self.threshold)

    def queue(self, limit: int = 20) -> dict[str, Any]:
        raw = [{"id": i.id, "last_review_ts": i.last_review_ts, "stability_days": i.stability_days} for i in self._items.values()]
        return review_queue(raw, threshold=self.threshold, limit=limit)

    def get(self, item_id: str) -> MemoryItem | None:
        return self._items.get(item_id)

    def __len__(self) -> int:
        return len(self._items)
