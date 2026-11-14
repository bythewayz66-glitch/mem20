"""Skills track for toolchest - second track alongside inventory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def _locate_skills_catalog() -> Path:
    for p in [SKILLS_DIR / "skills.catalog.agent.jsonl",
              Path("/opt/mem20/toolchest/skills/skills.catalog.agent.jsonl")]:
        if p.exists():
            return p
    return SKILLS_DIR / "skills.catalog.agent.jsonl"


DEFAULT_SKILLS = _locate_skills_catalog()


def load_skills(catalog: Optional[Path] = None) -> List[Dict[str, Any]]:
    cat = Path(catalog) if catalog else DEFAULT_SKILLS
    skills = []
    if cat.suffix == '.jsonl':
        for line in cat.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            skills.append(json.loads(line))
    elif cat.suffix == '.json':
        data = json.loads(cat.read_text())
        if isinstance(data, dict):
            skills = data.get('skills', [])
        elif isinstance(data, list):
            skills = data
    return skills


def load_skills_index(catalog: Optional[Path] = None) -> Dict[str, Any]:
    # look for index
    base = Path(catalog).parent if catalog else DEFAULT_SKILLS.parent
    for p in [base / "skills.index.agent.json", SKILLS_DIR / "skills.index.agent.json"]:
        if p.exists():
            return json.loads(p.read_text())
    return {}


def search_skills(term: str, catalog: Optional[Path] = None, limit: int = 100) -> List[Dict[str, Any]]:
    term_l = term.lower()
    skills = load_skills(catalog)
    idx = load_skills_index(catalog)
    hits = []
    # try index first
    if idx and 'inv' in idx:
        inv = idx['inv']
        # direct term match
        for k, ids in inv.items():
            if term_l in k.lower():
                # get those skills
                idset = set(ids)
                for s in skills:
                    if s['id'] in idset and s not in hits:
                        hits.append(s)
                        if len(hits) >= limit * 2:  # gather more then filter
                            pass
    # fallback text search
    if not hits:
        for s in skills:
            hay = json.dumps(s).lower()
            if term_l in hay:
                hits.append(s)
    # dedup
    seen = set()
    out = []
    for h in hits:
        if h['id'] in seen:
            continue
        seen.add(h['id'])
        out.append(h)
        if len(out) >= limit:
            break
    return out


def list_skills(ns: str = "", cat: str = "", catalog: Optional[Path] = None, limit: int = 200) -> List[Dict[str, Any]]:
    skills = load_skills(catalog)
    out = []
    for s in skills:
        if ns and s.get('ns','').lower() != ns.lower() and ns.lower() not in s.get('ns','').lower():
            continue
        if cat and s.get('cat','').lower() != cat.lower():
            continue
        out.append(s)
        if len(out) >= limit:
            break
    return out
