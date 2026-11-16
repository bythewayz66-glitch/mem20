"""The skill catalogue agents can discover and learn.

The canonical list lives in `src/data/templates/skills.ts`; it is exported to
`skill_catalogue.json` by `scripts/export-skills.mjs` so the server and the UI
share one source of truth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

CATALOGUE_PATH = Path(__file__).with_name("skill_catalogue.json")


def load_skill_catalogue() -> List[Dict[str, Any]]:
    try:
        raw = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key") or item.get("id") or "").strip()
        if not key:
            continue
        out.append(
            {
                "key": key,
                "label": str(item.get("label") or item.get("name") or key),
                "description": str(item.get("description") or ""),
                "category": str(item.get("category") or "general"),
            }
        )
    return out


def skill_status() -> Dict[str, Any]:
    skills = load_skill_catalogue()
    categories: Dict[str, int] = {}
    for s in skills:
        categories[s["category"]] = categories.get(s["category"], 0) + 1
    return {"count": len(skills), "categories": categories, "catalogue": str(CATALOGUE_PATH)}
