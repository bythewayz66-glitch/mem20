"""Outcome verification -- first-class memory_engine capability.

Verify predictions / claims against the grounded ledger and predictive outcomes.
Formerly mem20outcomeverificationruntimez.
"""
from __future__ import annotations

import time
from typing import Any


def verify_claim(
    topic: str,
    expected_content: str | None = None,
    *,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Check whether a topic has a grounded fact (optionally matching content)."""
    try:
        if as_of:
            from memory_engine import as_of as as_of_fn
            rows = as_of_fn(as_of, topic=topic, k=5, include_simulated=False)
        else:
            from memory_engine import recall
            rows = recall(topic=topic, k=5, include_simulated=False) or []
    except Exception as exc:
        return {"ok": False, "verified": False, "error": f"{type(exc).__name__}: {exc}"}
    if not rows:
        return {"ok": True, "verified": False, "reason": "no_grounded_fact", "topic": topic}
    if expected_content is None:
        return {"ok": True, "verified": True, "topic": topic, "fact_id": rows[0].get("id"), "content": rows[0].get("content")}
    exp = expected_content.lower()
    for r in rows:
        if exp in str(r.get("content") or "").lower():
            return {"ok": True, "verified": True, "topic": topic, "fact_id": r.get("id"), "content": r.get("content")}
    return {"ok": True, "verified": False, "reason": "content_mismatch", "topic": topic, "found": [r.get("content") for r in rows[:3]]}


def verify_prediction(
    prediction_id: str,
    used_fact_ids: list[str] | None = None,
    useful: bool = True,
) -> dict[str, Any]:
    """Record outcome on the predictive subsystem (engine-native)."""
    try:
        from memory_engine import record_recall_outcome
        oid = record_recall_outcome(prediction_id, used_fact_ids or [], useful)
        return {"ok": True, "outcome_id": oid, "prediction_id": prediction_id, "useful": useful}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def verify_batch(claims: list[dict[str, Any]]) -> dict[str, Any]:
    """claims: [{topic, expected_content?}]"""
    results = []
    ok_n = 0
    for c in claims or []:
        r = verify_claim(c.get("topic") or "", c.get("expected_content"))
        results.append(r)
        if r.get("verified"):
            ok_n += 1
    return {"total": len(results), "verified": ok_n, "results": results, "ts": time.time()}


def verify_health() -> dict[str, Any]:
    try:
        from memory_engine import predictive_health
        return {"ok": True, "predictive": predictive_health()}
    except Exception as exc:
        return {"ok": True, "predictive": None, "note": f"{type(exc).__name__}: {exc}"}
