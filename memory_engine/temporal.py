"""Temporal memory -- first-class memory_engine capability.

as-of recall is already in memory.recall_at. This module adds timeline,
diff, and grounded snapshot on top of the ledger -- formerly the
mem20memorytimemachinez subsystem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    topic: str
    content: str
    valid_from: str
    valid_to: str | None
    action: str
    origin: str = "grounded"


@dataclass(frozen=True)
class DiffResult:
    as_of_a: str
    as_of_b: str
    topic: str | None
    only_in_a: tuple[dict[str, Any], ...]
    only_in_b: tuple[dict[str, Any], ...]
    changed: tuple[dict[str, Any], ...]  # pairs encoded as {before, after}


def as_of(
    when: str | None = None,
    *,
    topic: str | None = None,
    tags: list[str] | None = None,
    k: int = 20,
    include_simulated: bool = False,
) -> list[dict[str, Any]]:
    """Recall ledger state as of an ISO timestamp (None = now).

    Thin public name over memory.recall_at. Defaults to grounded-only.
    """
    from memory_engine import recall_at
    return list(recall_at(
        as_of=when, topic=topic, tags=tags, k=k, include_simulated=include_simulated,
    ) or [])


def timeline(
    topic: str,
    *,
    since: str | None = None,
    until: str | None = None,
    k: int = 100,
    include_simulated: bool = False,
) -> list[TimelineEvent]:
    """Ordered history of a topic: remembers + supersessions visible on the ledger."""
    from memory_engine.memory import _load_ledger, _load_simulated_ledger, SUPERSEDED

    events: list[TimelineEvent] = []
    for r in _load_ledger() or []:
        if topic.lower() not in (r.get("topic") or "").lower():
            continue
        action = r.get("action") or ""
        if action not in ("remember", "supersede") and SUPERSEDED not in (r.get("content") or ""):
            if action != "remember":
                continue
        vf = r.get("valid_from") or r.get("ts") or ""
        if since and vf and vf < since:
            continue
        if until and vf and vf > until:
            continue
        events.append(TimelineEvent(
            id=str(r.get("id", "")),
            topic=str(r.get("topic", topic)),
            content=str(r.get("content", ""))[:500],
            valid_from=str(vf),
            valid_to=r.get("valid_to"),
            action=str(action or "remember"),
            origin="grounded",
        ))
    if include_simulated:
        for r in _load_simulated_ledger() or []:
            if topic.lower() not in (r.get("topic") or "").lower():
                continue
            if r.get("quarantined"):
                continue
            vf = r.get("valid_from") or r.get("ts") or ""
            if since and vf and vf < since:
                continue
            if until and vf and vf > until:
                continue
            events.append(TimelineEvent(
                id=str(r.get("id", "")),
                topic=str(r.get("topic", topic)),
                content=str(r.get("content", ""))[:500],
                valid_from=str(vf),
                valid_to=r.get("valid_to"),
                action=str(r.get("action") or "simulate"),
                origin="simulated",
            ))
    events.sort(key=lambda e: e.valid_from)
    return events[:k]


def diff(
    as_of_a: str,
    as_of_b: str,
    *,
    topic: str | None = None,
    k: int = 50,
    include_simulated: bool = False,
) -> DiffResult:
    """What changed in grounded (default) memory between two instants."""
    a = as_of(as_of_a, topic=topic, k=k * 2, include_simulated=include_simulated)
    b = as_of(as_of_b, topic=topic, k=k * 2, include_simulated=include_simulated)
    by_topic_content_a = {}
    by_topic_content_b = {}
    for r in a:
        key = (r.get("topic"), r.get("content"))
        by_topic_content_a[key] = r
    for r in b:
        key = (r.get("topic"), r.get("content"))
        by_topic_content_b[key] = r
    only_a = [r for key, r in by_topic_content_a.items() if key not in by_topic_content_b]
    only_b = [r for key, r in by_topic_content_b.items() if key not in by_topic_content_a]
    topics_a = {r.get("topic"): r for r in a}
    topics_b = {r.get("topic"): r for r in b}
    changed = []
    for t in set(topics_a) & set(topics_b):
        if topics_a[t].get("content") != topics_b[t].get("content"):
            changed.append({"before": topics_a[t], "after": topics_b[t]})
    return DiffResult(
        as_of_a=as_of_a,
        as_of_b=as_of_b,
        topic=topic,
        only_in_a=tuple(only_a[:k]),
        only_in_b=tuple(only_b[:k]),
        changed=tuple(changed[:k]),
    )


def snapshot(
    *,
    when: str | None = None,
    topic: str | None = None,
    k: int = 100,
    include_simulated: bool = False,
) -> dict[str, Any]:
    """Grounded ledger snapshot at `when` (None = now), plus engine health."""
    facts = as_of(when, topic=topic, k=k, include_simulated=include_simulated)
    health: dict[str, Any] = {}
    try:
        from memory_engine import index_health
        h = index_health()
        health = h if isinstance(h, dict) else {"raw": str(h)}
    except Exception as exc:
        health = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "as_of": when or "now",
        "grounded_only": not include_simulated,
        "count": len(facts),
        "facts": facts,
        "health": health,
    }


def temporal_health() -> dict[str, Any]:
    """Confirm recall_at and ledger are reachable."""
    try:
        from memory_engine import recall_at, index_health
        _ = recall_at(as_of=None, k=1, include_simulated=False)
        h = index_health()
        return {"ok": True, "recall_at": True, "index_health": h if isinstance(h, dict) else str(h)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
