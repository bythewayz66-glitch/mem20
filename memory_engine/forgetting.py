"""Ebbinghaus forgetting + spaced review on the grounded ledger.

Formerly mem20adaptiveforgettingenginez (via mem20adaptz.forgetting).
"""
from __future__ import annotations

import math
import time
from typing import Any

TOPIC_PREFIX = "forget:"


def retention(elapsed_days: float, stability_days: float) -> float:
    if stability_days <= 0:
        return 0.0
    return math.exp(-max(0.0, float(elapsed_days)) / float(stability_days))


def reinforce(
    stability_days: float,
    *,
    success: bool = True,
    growth: float = 1.8,
    decay: float = 0.4,
) -> float:
    s = max(1e-6, float(stability_days))
    return s * (growth if success else decay)


def _engine():
    from . import memory as eng
    return eng


def _now() -> float:
    return time.time()


def _parse_payload(content: str) -> dict[str, Any] | None:
    import ast
    try:
        v = ast.literal_eval(content)
        return v if isinstance(v, dict) else None
    except Exception:
        return None


def review_state(
    last_review_ts: float,
    stability_days: float,
    now_ts: float | None = None,
    threshold: float = 0.5,
) -> dict[str, Any]:
    now_ts = _now() if now_ts is None else now_ts
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


def track(
    item_id: str,
    content: str = "",
    *,
    stability_days: float = 1.0,
    tags: list[str] | None = None,
    epistemic_status: str = "observed",
) -> dict[str, Any]:
    eng = _engine()
    payload = {
        "id": item_id,
        "content": content,
        "stability_days": float(stability_days),
        "last_review_ts": _now(),
        "tags": list(tags or []),
    }
    topic = f"{TOPIC_PREFIX}{item_id}"
    fact = eng.remember(
        topic=topic,
        content=str(payload),
        epistemic_status=epistemic_status,
        tags=["forgetting", "spaced_review", *(tags or [])],
    )
    fid = getattr(fact, "id", None) or (fact.get("id") if isinstance(fact, dict) else None)
    return {"id": item_id, "topic": topic, "fact_id": fid, "stability_days": stability_days}


def _load_item(item_id: str) -> tuple[dict[str, Any], Any] | None:
    eng = _engine()
    topic = f"{TOPIC_PREFIX}{item_id}"
    facts = eng.recall(topic=topic, k=1)
    if not facts:
        return None
    f0 = facts[0]
    content = f0.content if hasattr(f0, "content") else f0.get("content", "")
    data = _parse_payload(content) or {}
    data.setdefault("id", item_id)
    data.setdefault("stability_days", 1.0)
    data.setdefault("last_review_ts", _now())
    return data, f0


def item_state(item_id: str, *, threshold: float = 0.5) -> dict[str, Any] | None:
    loaded = _load_item(item_id)
    if not loaded:
        return None
    it, _ = loaded
    st = review_state(it["last_review_ts"], it.get("stability_days", 1.0), threshold=threshold)
    st["id"] = item_id
    st["content"] = it.get("content", "")
    return st


def review(
    item_id: str,
    *,
    success: bool = True,
    epistemic_status: str = "observed",
) -> dict[str, Any]:
    eng = _engine()
    loaded = _load_item(item_id)
    if not loaded:
        return {"ok": False, "error": "not_found", "id": item_id}
    it, f0 = loaded
    new_s = reinforce(it.get("stability_days", 1.0), success=success)
    it["stability_days"] = new_s
    it["last_review_ts"] = _now()
    topic = f"{TOPIC_PREFIX}{item_id}"
    fid = f0.id if hasattr(f0, "id") else f0.get("id")
    if fid:
        try:
            eng.supersede(str(fid), str(it), tags=["forgetting", "spaced_review"])
        except Exception:
            eng.remember(topic=topic, content=str(it), epistemic_status=epistemic_status)
    else:
        eng.remember(topic=topic, content=str(it), epistemic_status=epistemic_status)
    st = review_state(it["last_review_ts"], new_s)
    st["id"] = item_id
    st["ok"] = True
    return st


def review_queue(*, threshold: float = 0.5, limit: int = 20) -> dict[str, Any]:
    eng = _engine()
    facts = eng.recall(k=500)
    scored = []
    for f in facts:
        topic = f.topic if hasattr(f, "topic") else f.get("topic", "")
        if not str(topic).startswith(TOPIC_PREFIX):
            continue
        content = f.content if hasattr(f, "content") else f.get("content", "")
        data = _parse_payload(content) or {}
        if "last_review_ts" not in data:
            continue
        st = review_state(data["last_review_ts"], data.get("stability_days", 1.0), threshold=threshold)
        st["id"] = data.get("id") or str(topic)[len(TOPIC_PREFIX) :]
        scored.append(st)
    scored.sort(key=lambda s: s["retention"])
    due = [s for s in scored if not s["retrievable"]]
    return {"due_count": len(due), "queue": due[:limit], "tracked": len(scored)}


def forgetting_health() -> dict[str, Any]:
    q = review_queue(limit=5)
    return {"ok": True, "module": "forgetting", "tracked": q["tracked"], "due_count": q["due_count"]}


__all__ = [
    "retention",
    "reinforce",
    "review_state",
    "track",
    "item_state",
    "review",
    "review_queue",
    "forgetting_health",
]
