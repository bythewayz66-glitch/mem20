"""mem20facez domain: 8-member interface/workspace runtime registry and composition planning."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import importlib, time

MEMBERS = (
    "mem20adaptiveinterfacecomposerz","mem20musicvisualsynchronizerz","mem20parallelworkstreamcomposerz",
    "mem20spatialcommanduniversez","mem20spatialexperiencedesignerz","mem20visualagentblackboardz",
    "mem20visualdataflowcomposerz","mem20voicetoactionswitchboardz",
)

@dataclass
class MemberStatus:
    name: str; importable: bool; version: Optional[str] = None; error: Optional[str] = None; checked_at: float = field(default_factory=time.time)

@dataclass
class CompositionPlan:
    intent: str; selected: List[str]; layout: str; confidence: float; reasons: List[str]

def check_member(name: str) -> MemberStatus:
    try:
        mod = importlib.import_module(name); ver = getattr(mod, "__version__", None)
        return MemberStatus(name=name, importable=True, version=str(ver) if ver is not None else None)
    except Exception as e:
        return MemberStatus(name=name, importable=False, error=f"{type(e).__name__}: {e}")

def probe_members(names=None): return [check_member(n) for n in (names or list(MEMBERS))]

def compose_plan(intent: str = "workspace", payload: Dict[str, Any] = None) -> CompositionPlan:
    payload = payload or {}; text = f"{intent} {payload.get('mode','')} {payload.get('input','')}".lower()
    scored = []
    for m in MEMBERS:
        score = 0.1
        if "visual" in m and ("visual" in text or "data" in text or "board" in text): score += 2
        if "spatial" in m and ("spatial" in text or "3d" in text): score += 2
        if "voice" in m and ("voice" in text or "audio" in text): score += 2
        if "parallel" in m and ("parallel" in text or "stream" in text): score += 2
        if "adaptive" in m or "interface" in m: score += 1
        if "music" in m and "music" in text: score += 2
        scored.append((score, m))
    scored.sort(key=lambda x: (-x[0], x[1]))
    selected = [m for s, m in scored[:4]]
    layout = "spatial" if "spatial" in text else ("visual" if "visual" in text else "adaptive")
    return CompositionPlan(intent=intent, selected=selected, layout=layout, confidence=round(min(0.99, 0.5 + 0.1*len([s for s,_ in scored if s>1])),4), reasons=[f"layout={layout}", f"selected={len(selected)}"])
