"""Engine runtime domain: real member registry, probing, compatibility, dispatch.

Assimilated runtime: members include all absorbed subsystems rehomed under
mem20enginez/absorbed/ (canonical + locally held copies). Probing locates
absorbed members on disk and via import, and ecosystem peer aggregation
surfaces peers from absorbed member ecosystems (>> 6).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
import importlib
import json
import sys
import time
import uuid


ESTATE_ROOT = Path(__file__).resolve().parents[2]
ABSORBED_ROOT = Path(__file__).resolve().parents[1] / "absorbed"
_TOOLCHEST_SRC = ESTATE_ROOT / "toolchest" / "src"


def _ensure_paths() -> None:
    root = str(ESTATE_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    tc = str(_TOOLCHEST_SRC)
    if _TOOLCHEST_SRC.is_dir() and tc not in sys.path:
        sys.path.insert(0, tc)
    # ensure absorbed finder active
    try:
        import _mem20_absorbed_finder  # noqa: F401
    except Exception:
        try:
            spec = importlib.util.spec_from_file_location(
                "_mem20_absorbed_finder", ESTATE_ROOT / "_mem20_absorbed_finder.py"
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore
                sys.modules.setdefault("_mem20_absorbed_finder", mod)
        except Exception:
            pass


_ensure_paths()


def _discover_absorbed() -> tuple[str, ...]:
    if not ABSORBED_ROOT.is_dir():
        return ()
    names = []
    for p in sorted(ABSORBED_ROOT.iterdir()):
        if p.is_dir() and p.name.startswith("mem20") and p.name.endswith("z"):
            names.append(p.name)
    return tuple(names)


MEMBERS: tuple[str, ...] = _discover_absorbed() or (
    "mem20runtimebugpredictionenginez", "mem20crosslanguagerefactorenginez", "mem20chaosnativeapplicationruntimez",
    "mem20crdtcollaborationenginez", "mem20generativebrandworldenginez", "mem20liveschemamorphingenginez",
    "mem20multilingualliveconversationenginez", "mem20communitypulseenginez", "mem20peertopeerappruntimez",
    "mem20featuredependencygraphenginez", "mem20privatelocalreasoningenginez", "mem20outcomeverificationruntimez",
    "mem20completionconfidenceenginez", "mem20mobileedgeagentruntimez", "mem20devicecapabilitycompilerz",
    "mem20protocolautodiscoveryenginez", "mem20runtimecompatibilityenginez", "mem20speculativeworkflowenginez",
    "mem20servicebundlingenginez", "mem20predictiverecallenginez", "mem20customerlifecycleenginez",
    "mem20autonomousdealdeskz", "mem20communitychallengeenginez", "mem20dynamicnarrativeenginez",
    "mem20liveprojectdemonstrationenginez", "mem20memorytimemachinez", "mem20offergenomeenginez",
    "mem20selfhealingplansz", "mem20zerotouchnodeswarmz", "mem20mixedinitiativefocusenginez",
    "mem20webhooksupernetworkz",
)


@dataclass(frozen=True)
class EngineMember:
    name: str
    package: str
    kind: str = "engine"
    absorbed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MemberStatus:
    name: str
    present: bool
    importable: bool
    absorbed: bool = False
    version: Optional[str] = None
    error: Optional[str] = None
    path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimePlan:
    plan_id: str
    intent: str
    members: List[str]
    steps: List[Dict[str, Any]]
    signals: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RuntimeReport:
    ok: bool
    members_total: int
    members_present: int
    members_importable: int
    absorbed_total: int
    statuses: List[MemberStatus]
    generated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["statuses"] = [s.to_dict() if hasattr(s, "to_dict") else s for s in self.statuses]
        return d


def member_registry(names: Sequence[str] = None) -> List[EngineMember]:
    names = list(names or MEMBERS)
    out = []
    for n in names:
        absorbed = (ABSORBED_ROOT / n).is_dir()
        out.append(EngineMember(name=n, package=n, absorbed=absorbed))
    return out


def _member_dir(name: str, root: Path = None) -> Optional[Path]:
    base = Path(root) if root else ESTATE_ROOT
    # absorbed under this runtime first
    p = ABSORBED_ROOT / name
    if p.is_dir():
        return p
    # legacy standalone location
    p2 = base / name
    if p2.is_dir():
        return p2
    # try canonical absorbed location via finder map
    try:
        mp = base / ".mem20-absorbed-map.json"
        if mp.exists():
            data = json.loads(mp.read_text())
            loc = (data.get("mapping") or {}).get(name)
            if loc:
                # mapping points to inner package dir; absorbed root is parent of package dir
                lp = Path(loc)
                if lp.is_dir():
                    return lp.parent
    except Exception:
        pass
    return None


def check_member(name: str, root: Path = None) -> MemberStatus:
    _ensure_paths()
    p = _member_dir(name, root)
    present = p is not None
    absorbed = (ABSORBED_ROOT / name).is_dir()
    ver = None
    err = None
    importable = False
    try:
        mod = importlib.import_module(name)
        importable = True
        ver = getattr(mod, "__version__", None)
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
    return MemberStatus(name=name, present=present, importable=importable, absorbed=absorbed,
                        version=str(ver) if ver is not None else None, error=err,
                        path=str(p) if p else None)


def summarize(statuses: Sequence[MemberStatus]) -> RuntimeReport:
    st = list(statuses)
    present = [s for s in st if s.present]
    imp = [s for s in st if s.importable]
    absorbed = [s for s in st if getattr(s, 'absorbed', False)]
    ok = len(present) == len(st) and len(st) > 0
    return RuntimeReport(ok=ok, members_total=len(st), members_present=len(present),
                         members_importable=len(imp), absorbed_total=len(absorbed), statuses=st)


def compatibility(members: Sequence[str] = None) -> Dict[str, Any]:
    members = list(members or MEMBERS)
    statuses = [check_member(n) for n in members]
    rep = summarize(statuses)
    issues = [{"member": s.name, "error": s.error} for s in statuses if not s.importable]
    return {"ok": rep.ok, "members": len(members), "importable": rep.members_importable,
            "issues": issues, "report": rep.to_dict()}


def dispatch_plan(intent: str, statuses: Sequence[MemberStatus] = None, limit: int = 12) -> RuntimePlan:
    statuses = list(statuses or [check_member(n) for n in MEMBERS])
    ok_members = [s.name for s in statuses if s.present or s.importable]
    intent_l = (intent or "").lower()
    scored = []
    for name in ok_members:
        score = 0
        nl = name.lower()
        for token in intent_l.replace('-', ' ').replace('_', ' ').split():
            if token and token in nl:
                score += 2
        # heuristic boosts
        for key in ("runtime", "compat", "protocol", "dispatch", "speculat", "predict", "recall",
                    "service", "bundle", "lifecycle", "deal", "swarm", "healing", "webhook"):
            if key in intent_l and key in nl:
                score += 3
        scored.append((score, name))
    scored.sort(key=lambda x: (-x[0], x[1]))
    selected = [n for s, n in scored if s > 0][:limit]
    if not selected:
        selected = ok_members[: min(limit, len(ok_members))]
    steps = []
    for i, name in enumerate(selected, 1):
        steps.append({"step": i, "member": name, "action": "probe/dispatch", "intent": intent})
    signals = {"selected": len(selected), "intent_tokens": len(intent_l.split()), "total_members": len(statuses)}
    return RuntimePlan(plan_id=str(uuid.uuid4()), intent=intent, members=selected, steps=steps, signals=signals)
