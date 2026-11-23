"""Session continuity -- first-class memory_engine capability.

Persist agent/device session state on the grounded ledger.
Formerly mem20crossdevicesessioncontinuityz.
"""
from __future__ import annotations

import json
import time
from typing import Any


def _topic(session_id: str) -> str:
    return f"session:{session_id}"


def save_session(
    session_id: str,
    state: dict[str, Any],
    *,
    device_id: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Save session state as a grounded fact (supersedes prior version)."""
    payload = {
        "session_id": session_id,
        "device_id": device_id,
        "state": state or {},
        "updated_at": time.time(),
    }
    try:
        from memory_engine import remember, recall, supersede
        prev = recall(topic=_topic(session_id), k=1, include_simulated=False) or []
        body = json.dumps(payload)
        tag_list = list(tags or []) + ["session", session_id]
        if device_id:
            tag_list.append(device_id)
        if prev and prev[0].get("id"):
            row = supersede(prev[0]["id"], body, epistemic_status="observed")
            return {"ok": True, "session_id": session_id, "id": (row or {}).get("id") if isinstance(row, dict) else prev[0].get("id"), "updated": True}
        row = remember(topic=_topic(session_id), content=body, tags=tag_list, epistemic_status="observed")
        return {"ok": True, "session_id": session_id, "id": row.get("id") if isinstance(row, dict) else None, "updated": False}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "session_id": session_id}


def load_session(session_id: str) -> dict[str, Any]:
    try:
        from memory_engine import recall
        rows = recall(topic=_topic(session_id), k=1, include_simulated=False) or []
        if not rows:
            return {"ok": False, "error": "not_found", "session_id": session_id}
        data = json.loads(rows[0].get("content") or "{}")
        data["ok"] = True
        data["_fact_id"] = rows[0].get("id")
        return data
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "session_id": session_id}


def list_sessions(*, k: int = 20) -> list[dict[str, Any]]:
    try:
        from memory_engine import recall
        rows = recall(topic="session:", k=k, include_simulated=False) or []
    except Exception:
        return []
    out = []
    for r in rows:
        try:
            data = json.loads(r.get("content") or "{}")
            data["_fact_id"] = r.get("id")
            out.append(data)
        except Exception:
            continue
    return out


def session_health() -> dict[str, Any]:
    return {"ok": True, "sessions": len(list_sessions(k=5))}
