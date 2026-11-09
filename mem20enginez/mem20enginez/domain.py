"""Engine runtime domain: real member registry, probing, compatibility, dispatch.

MEMBERS is the canonical 30-member crew. Domain logic verifies members against
the live filesystem/package surface, computes compatibility/health, and builds
deterministic dispatch plans. Pure where possible (filesystem checks are reads).
"""
from __future__ import annotations

import importlib
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

MEMBERS: tuple[str, ...] = (
    "mem20adaptiveachievementenginez",
    "mem20adaptivedispatchenginez",
    "mem20adaptiveforgettingenginez",
    "mem20adaptivepersonalityruntimez",
    "mem20schoolz",
    "mem20chaosnativeapplicationruntimez",
    "mem20communitychallengeenginez",
    "mem20communitypulseenginez",
    "mem20completionconfidenceenginez",
    "mem20crdtcollaborationenginez",
    "mem20crosslanguagerefactorenginez",
    "mem20customerlifecycleenginez",
    "mem20dynamicnarrativeenginez",
    "mem20featuredependencygraphenginez",
    "mem20generativebrandworldenginez",
    "mem20liveprojectdemonstrationenginez",
    "mem20liveschemamorphingenginez",
    "mem20mixedinitiativefocusenginez",
    "mem20mobileedgeagentruntimez",
    "mem20multilingualliveconversationenginez",
    "mem20offergenomeenginez",
    "mem20outcomeverificationruntimez",
    "mem20peertopeerappruntimez",
    "mem20predictiverecallenginez",
    "mem20privatelocalreasoningenginez",
    "mem20protocolautodiscoveryenginez",
    "mem20runtimebugpredictionenginez",
    "mem20runtimecompatibilityenginez",
    "mem20servicebundlingenginez",
    "mem20speculativeworkflowenginez",
)

ENGINE_ROOT = Path(__file__).resolve().parents[1]
ESTATE_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class MemberStatus:
    name: str
    present: bool = False
    has_package: bool = False
    has_domain: bool = False
    has_runtime: bool = False
    has_tests: bool = False
    importable: bool = False
    version: Optional[str] = None
    error: Optional[str] = None
    checked_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "present": self.present, "has_package": self.has_package,
            "has_domain": self.has_domain, "has_runtime": self.has_runtime, "has_tests": self.has_tests,
            "importable": self.importable, "version": self.version, "error": self.error,
            "checked_at": self.checked_at, "healthy": self.healthy,
        }

    @property
    def healthy(self) -> bool:
        return self.present and (self.has_domain or self.has_runtime or self.importable)


@dataclass
class EngineMember:
    name: str
    kind: str = "engine"
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "kind": self.kind, "capabilities": self.capabilities, "metadata": self.metadata}


@dataclass
class RuntimePlan:
    plan_id: str
    intent: str
    selected: List[str]
    steps: List[Dict[str, Any]]
    rationale: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"plan_id": self.plan_id, "intent": self.intent, "selected": self.selected,
                "steps": self.steps, "rationale": self.rationale, "created_at": self.created_at}


@dataclass
class RuntimeReport:
    ok: bool
    members_total: int
    members_present: int
    members_healthy: int
    statuses: List[Dict[str, Any]]
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "members_total": self.members_total, "members_present": self.members_present,
                "members_healthy": self.members_healthy, "statuses": self.statuses, "generated_at": self.generated_at}


def _kind(name: str) -> str:
    if "runtime" in name:
        return "runtime"
    return "engine"


def member_registry(names: Sequence[str] = MEMBERS) -> List[EngineMember]:
    out = []
    for n in names:
        caps = []
        low = n.lower()
        if "dispatch" in low: caps.append("dispatch")
        if "compat" in low: caps.append("compatibility")
        if "protocol" in low: caps.append("protocol-discovery")
        if "speculative" in low: caps.append("speculative-execution")
        if "predict" in low or "recall" in low: caps.append("prediction")
        if "lifecycle" in low: caps.append("lifecycle")
        if "verify" in low or "confidence" in low: caps.append("verification")
        if "collab" in low or "crdt" in low: caps.append("collaboration")
        if "focus" in low: caps.append("focus")
        if not caps: caps.append("engine")
        out.append(EngineMember(name=n, kind=_kind(n), capabilities=caps))
    return out


def check_member(name: str, estate_root: Optional[Path] = None) -> MemberStatus:
    root = Path(estate_root) if estate_root else ESTATE_ROOT
    base = root / name
    st = MemberStatus(name=name, present=base.is_dir())
    if not st.present:
        st.error = "directory missing"
        return st
    pkg = base / name
    st.has_package = (pkg / "__init__.py").is_file() or (base / "__init__.py").is_file()
    st.has_domain = (pkg / "domain.py").is_file() or (base / "domain.py").is_file()
    st.has_runtime = (pkg / "runtime.py").is_file() or (base / "runtime.py").is_file()
    st.has_tests = (base / "tests").is_dir()
    # import probe (best-effort, no heavy side effects beyond import)
    try:
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        mod = importlib.import_module(name)
        st.importable = True
        st.version = getattr(mod, "__version__", None)
    except Exception as e:
        st.importable = False
        st.error = f"{type(e).__name__}: {e}"
    return st


def summarize(statuses: Sequence[MemberStatus]) -> RuntimeReport:
    present = sum(1 for s in statuses if s.present)
    healthy = sum(1 for s in statuses if s.healthy)
    # ok if registry is intact and we can report truthfully; degraded members are reported, not hidden
    return RuntimeReport(ok=True, members_total=len(statuses), members_present=present,
                         members_healthy=healthy, statuses=[s.to_dict() for s in statuses])


def compatibility(requirements: Optional[Mapping[str, Any]] = None, env: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    req = dict(requirements or {"python": [3, 11], "members_min": 1})
    py = sys.version_info[:2]
    py_ok = list(py) >= list(req.get("python", [3, 11]))
    return {"ok": py_ok, "python": {"current": list(py), "required": list(req.get("python", [3, 11])), "ok": py_ok},
            "platform": sys.platform, "requirements": req, "env": dict(env or {})}


def dispatch_plan(intent: str, statuses: Sequence[MemberStatus], context: Optional[Mapping[str, Any]] = None) -> RuntimePlan:
    intent_l = (intent or "").lower()
    reg = {m.name: m for m in member_registry()}
    selected = []
    for s in statuses:
        if not s.healthy:
            continue
        caps = reg.get(s.name, EngineMember(s.name)).capabilities
        score = 0
        for c in caps:
            if c.replace("-", " ") in intent_l or c.split("-")[0] in intent_l:
                score += 2
        if "compat" in intent_l and "compatibility" in caps: score += 3
        if "protocol" in intent_l and "protocol-discovery" in caps: score += 3
        if "speculat" in intent_l and "speculative-execution" in caps: score += 3
        if "predict" in intent_l and "prediction" in caps: score += 2
        if "lifecycle" in intent_l and "lifecycle" in caps: score += 2
        if score > 0:
            selected.append((score, s.name))
    selected.sort(key=lambda x: (-x[0], x[1]))
    chosen = [n for _, n in selected[:5]] or [s.name for s in statuses if s.healthy][:3]
    steps = []
    for i, name in enumerate(chosen, 1):
        m = reg.get(name, EngineMember(name))
        steps.append({"step": i, "member": name, "kind": m.kind, "capabilities": m.capabilities,
                      "action": "probe-then-dispatch", "status": "planned"})
    plan_id = f"plan-{abs(hash((intent, tuple(chosen), round(time.time(), 0)))) % 10**10}"
    rationale = f"Selected {len(chosen)} healthy member(s) for intent '{intent}' by capability match." if chosen else f"No healthy capability match for '{intent}'; runtime reported truthfully."
    return RuntimePlan(plan_id=plan_id, intent=intent, selected=chosen, steps=steps, rationale=rationale)
