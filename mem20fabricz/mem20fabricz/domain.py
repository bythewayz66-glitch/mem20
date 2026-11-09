"""mem20fabricz domain: 23-member integration fabric registry, probing, dispatch planning."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import importlib, time

MEMBERS = (
    "mem20apishapeshiftinggatewayz","mem20rewardforgez","mem20collectivemodelintelligencez",
    "mem20rewardforgez","mem20crisisresponsemeshz","mem20crossruntimeeventlatticez",
    "mem20edgetransportfabricz","mem20eventstreamsuperhighwayz","mem20federatedmodellearningmeshz",
    "mem20freestackambientcomputingfabricz","mem20livemodelfusionz","mem20modalitybridgez",
    "mem20modelsleepandwakesystemz","mem20nearbydevicemeshz","mem20offlineresiliencemeshz",
    "mem20personalmodelevolutionz","mem20planetarybatchfabricz","mem20rewardforgez",
    "mem20sensorfusiongatewayz","mem20rewardforgez","mem20rewardforgez",
    "mem20temporaldatabasefabricz","mem20universalintegrationcompilerz",
)

@dataclass
class MemberStatus:
    name: str
    importable: bool
    version: Optional[str] = None
    error: Optional[str] = None
    checked_at: float = field(default_factory=time.time)

@dataclass
class DispatchPlan:
    route: str
    selected: List[str]
    fallbacks: List[str]
    confidence: float
    reasons: List[str]

@dataclass
class FabricReport:
    members: int
    importable: int
    unavailable: int
    statuses: List[MemberStatus]
    plan: Optional[DispatchPlan] = None
    signals: Dict[str, Any] = field(default_factory=dict)

def check_member(name: str) -> MemberStatus:
    try:
        mod = importlib.import_module(name)
        ver = getattr(mod, "__version__", None)
        return MemberStatus(name=name, importable=True, version=str(ver) if ver is not None else None)
    except Exception as e:
        return MemberStatus(name=name, importable=False, error=f"{type(e).__name__}: {e}")

def probe_members(names: List[str] = None) -> List[MemberStatus]:
    return [check_member(n) for n in (names or list(MEMBERS))]

def dispatch_plan(intent: str = "integrate", payload: Dict[str, Any] = None) -> DispatchPlan:
    payload = payload or {}
    text = f"{intent} {payload.get('kind','')} {payload.get('target','')}".lower()
    scored = []
    for m in MEMBERS:
        score = 0
        toks = [t for t in m.replace('mem20','').replace('z',' ').split() if t]
        for t in toks:
            if t and t in text: score += 2
        if "integrat" in m and "integrat" in text: score += 2
        if "event" in m and "event" in text: score += 2
        if "gateway" in m and ("api" in text or "gateway" in text): score += 2
        if "mesh" in m and ("resilien" in text or "offline" in text or "crisis" in text): score += 2
        if "model" in m and "model" in text: score += 1
        if "fabric" in m or "transport" in m: score += 0.1
        scored.append((score, m))
    scored.sort(key=lambda x: (-x[0], x[1]))
    selected = [m for s, m in scored if s > 0][:3] or [scored[0][1]]
    fallbacks = [m for m in MEMBERS if m not in selected][:3]
    conf = min(0.99, 0.45 + 0.15 * len([s for s, _ in scored if s > 0]))
    reasons = [f"matched intent={intent}", f"selected={len(selected)}"]
    return DispatchPlan(route=intent, selected=selected, fallbacks=fallbacks, confidence=round(conf,4), reasons=reasons)

def summarize(statuses: List[MemberStatus], plan: DispatchPlan = None, signals: Dict[str, Any] = None) -> FabricReport:
    ok = [s for s in statuses if s.importable]
    return FabricReport(members=len(statuses), importable=len(ok), unavailable=len(statuses)-len(ok),
                        statuses=statuses, plan=plan, signals=signals or {})
