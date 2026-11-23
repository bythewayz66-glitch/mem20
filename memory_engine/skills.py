"""Skill memory transfer -- first-class memory_engine capability.

Export/import procedural skills as grounded facts. Formerly mem20skillmemorytransferz.
"""
from __future__ import annotations

import json
from typing import Any


def _skill_topic(name: str) -> str:
    return f"skill:{name}"


def export_skill(name: str, *, actor: str = "agent") -> dict[str, Any]:
    """Export a procedural skill (from engine procedural store or ledger)."""
    skill = None
    try:
        from memory_engine import procedural_get_skill
        skill = procedural_get_skill(name, actor=actor)
        if isinstance(skill, dict) and skill.get("error"):
            skill = None
    except Exception:
        skill = None
    if skill is None:
        try:
            from memory_engine import recall
            rows = recall(topic=_skill_topic(name), k=1, include_simulated=False) or []
            if rows:
                skill = json.loads(rows[0].get("content") or "{}")
                skill["_fact_id"] = rows[0].get("id")
        except Exception:
            pass
    if not skill:
        return {"ok": False, "error": "missing", "name": name}
    return {"ok": True, "name": name, "skill": skill}


def import_skill(skill: dict[str, Any], *, actor: str = "agent", persist: bool = True) -> dict[str, Any]:
    """Import a skill dict into procedural memory and optionally the ledger."""
    name = str(skill.get("name") or skill.get("id") or "").strip()
    if not name:
        return {"ok": False, "error": "skill needs name"}
    try:
        from memory_engine import procedural_add_skill
        try:
            procedural_add_skill(
                name=name,
                description=str(skill.get("description") or ""),
                steps=list(skill.get("steps") or []),
            )
        except TypeError:
            procedural_add_skill(name, str(skill.get("description") or ""), list(skill.get("steps") or []))
    except Exception as exc:
        return {"ok": False, "error": f"procedural: {type(exc).__name__}: {exc}", "name": name}
    if persist:
        try:
            from memory_engine import remember
            remember(
                topic=_skill_topic(name),
                content=json.dumps({k: v for k, v in skill.items() if not str(k).startswith("_")}),
                tags=["skill", "transfer", name],
                epistemic_status="observed",
            )
        except Exception as exc:
            return {"ok": True, "name": name, "persisted": False, "warn": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "name": name, "persisted": persist}


def transfer_skill(name: str, *, actor: str = "agent") -> dict[str, Any]:
    """Export then re-import (round-trip / copy into ledger)."""
    exp = export_skill(name, actor=actor)
    if not exp.get("ok"):
        return exp
    return import_skill(exp["skill"], actor=actor, persist=True)


def list_transferred_skills(*, k: int = 50) -> list[dict[str, Any]]:
    try:
        from memory_engine import recall
        rows = recall(topic="skill:", k=k, include_simulated=False) or []
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


def skills_health() -> dict[str, Any]:
    return {"ok": True, "transferred": len(list_transferred_skills(k=5)), "backend": "procedural+ledger"}
