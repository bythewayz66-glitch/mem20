"""Domain logic for mem20graphz crew runtime: graph composition and member health."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import importlib
from . import MEMBERS, __version__

@dataclass
class MemberReport:
    name: str
    importable: bool
    error: str | None = None

def probe_members(names=None) -> List[Dict[str, Any]]:
    out = []
    for name in (names or list(MEMBERS)):
        try:
            importlib.import_module(name)
            out.append(asdict(MemberReport(name=name, importable=True)))
        except Exception as e:
            out.append(asdict(MemberReport(name=name, importable=False, error=f"{type(e).__name__}: {e}")))
    return out

def crew_summary(member_reports: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    reps = member_reports if member_reports is not None else probe_members()
    ok = sum(1 for r in reps if r.get("importable"))
    return {"crew": "mem20graphz", "version": __version__, "members": len(reps), "importable": ok, "reports": reps}
