"""Pipeline 1 — Game Concept, GDD & Scope.

Rebuilt to the pipeline-1 spec: a structured concept brief (title, pitch,
audience, platform targets, core loop, feature list, risks, milestones,
success criteria), plus detection of contradictions, uncontrolled scope,
missing success criteria, and features that do not support the core
experience, and a controlled GDD render.

Stdlib only by design — pipeline 1 must stand alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

CORE_PARTS = ("action", "feedback", "reward", "progression")
CRITERIA_KINDS = ("measurable", "timebound", "player_visible")
VALID_SEVERITIES = ("low", "medium", "high", "critical")

# A peripheral feature may not take more than this share of total effort.
PERIPHERAL_SHARE_LIMIT = 0.25
# An optional feature costing more than this share of budget is "fat".
FAT_OPTIONAL_SHARE = 0.15
# Total planned effort above this multiple of budget is unrealistic.
UNREALISTIC_MULTIPLE = 2.0

_STOPWORDS = frozenset(
    """a an the and or but of in on at to for with without where when which
    that this these those is are was were be been being it its as by from
    into over under than then them they their there here you your yours we
    our ours theyre let lets can could will would should may might must do
    does did done have has had not no yes per each every very just also""".split()
)

_VR_TOKENS = ("quest", "vr", "psvr", "oculus", "vive", "headset", "index")
_PC_TOKENS = ("windows", "linux", "macos", "mac", "pc", "steam", "desktop")


class ConceptError(ValueError):
    """Raised when a concept cannot be turned into a usable brief."""


# ── model ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CoreLoop:
    action: str = ""
    feedback: str = ""
    reward: str = ""
    progression: str = ""
    duration_seconds: int | None = None

    def is_complete(self) -> bool:
        return all(str(getattr(self, p) or "").strip() for p in CORE_PARTS)

    def as_text(self) -> str:
        return " ".join(str(getattr(self, p) or "") for p in CORE_PARTS)

    def missing(self) -> list[str]:
        return [p for p in CORE_PARTS if not str(getattr(self, p) or "").strip()]


@dataclass(frozen=True)
class Feature:
    id: str
    name: str
    supports: list[str] = field(default_factory=list)
    effort_days: float = 0.0
    core: bool = False
    must_have: bool = False

    @property
    def is_optional(self) -> bool:
        return not self.must_have

    @property
    def is_peripheral(self) -> bool:
        return not self.supports


@dataclass(frozen=True)
class Risk:
    id: str
    description: str
    severity: str = "medium"
    likelihood: str = "medium"
    mitigation: str = ""

    @property
    def mitigated(self) -> bool:
        return bool(self.mitigation.strip())


@dataclass(frozen=True)
class Milestone:
    id: str
    name: str
    depends_on: list[str] = field(default_factory=list)
    exit_criteria: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SuccessCriterion:
    id: str
    statement: str
    kind: str = "measurable"
    metric: str = ""
    threshold: str = ""

    @property
    def is_usable(self) -> bool:
        """A criterion only counts if it says how it will be judged."""
        return bool(str(self.metric).strip()) and bool(
            str(self.threshold).strip()
        )


@dataclass(frozen=True)
class Brief:
    title: str
    pitch: str
    audience: list[str]
    platforms: list[str]
    core_loop: CoreLoop
    features: list[Feature]
    risks: list[Risk]
    milestones: list[Milestone]
    success_criteria: list[SuccessCriterion]

    @property
    def total_effort_days(self) -> float:
        return float(sum(f.effort_days for f in self.features))


@dataclass(frozen=True)
class Contradiction:
    code: str
    severity: str
    detail: str


@dataclass(frozen=True)
class ScopeFinding:
    code: str
    severity: str
    detail: str
    impact_days: float = 0.0


# ── construction ─────────────────────────────────────────────────────────────


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _norm_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip().lower()] if value.strip() else []
    return [_text(v).lower() for v in value if _text(v)]


def _core_loop(raw: Any) -> CoreLoop:
    if not isinstance(raw, Mapping):
        return CoreLoop()
    duration = raw.get("duration_seconds")
    try:
        duration = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration = None
    return CoreLoop(
        action=_text(raw.get("action")),
        feedback=_text(raw.get("feedback")),
        reward=_text(raw.get("reward")),
        progression=_text(raw.get("progression")),
        duration_seconds=duration,
    )


def build_brief(raw: Mapping[str, Any]) -> Brief:
    """Normalise a raw concept mapping into a validated Brief."""
    if not isinstance(raw, Mapping):
        raise ConceptError("concept must be a mapping")

    title = _text(raw.get("title"))
    pitch = _text(raw.get("pitch"))
    if not title:
        raise ConceptError("concept needs a title")
    if not pitch:
        raise ConceptError("concept needs a pitch")

    features: list[Feature] = []
    seen_features: set[str] = set()
    for item in raw.get("features") or []:
        if not isinstance(item, Mapping):
            continue
        fid = _text(item.get("id"))
        if not fid:
            raise ConceptError("feature is missing an id")
        if fid in seen_features:
            raise ConceptError(f"duplicate feature id {fid}")
        seen_features.add(fid)
        try:
            effort = float(item.get("effort_days") or 0)
        except (TypeError, ValueError) as exc:
            raise ConceptError(f"bad effort_days on {fid}") from exc
        features.append(
            Feature(
                id=fid,
                name=_text(item.get("name")) or fid,
                supports=[_text(s).lower() for s in item.get("supports") or []],
                effort_days=effort,
                core=bool(item.get("core", False)),
                must_have=bool(item.get("must_have", False)),
            )
        )

    risks: list[Risk] = []
    for item in raw.get("risks") or []:
        if not isinstance(item, Mapping):
            continue
        severity = _text(item.get("severity")).lower() or "medium"
        if severity not in VALID_SEVERITIES:
            raise ConceptError(
                f"bad severity {severity!r} — expected one of "
                f"{', '.join(VALID_SEVERITIES)}"
            )
        likelihood = _text(item.get("likelihood")).lower() or "medium"
        if likelihood not in VALID_SEVERITIES:
            raise ConceptError(f"bad likelihood {likelihood!r}")
        risks.append(
            Risk(
                id=_text(item.get("id")) or f"R{len(risks) + 1:03d}",
                description=_text(item.get("description")),
                severity=severity,
                likelihood=likelihood,
                mitigation=_text(item.get("mitigation")),
            )
        )

    milestones: list[Milestone] = []
    for item in raw.get("milestones") or []:
        if not isinstance(item, Mapping):
            continue
        milestones.append(
            Milestone(
                id=_text(item.get("id")),
                name=_text(item.get("name")),
                depends_on=[_text(d) for d in item.get("depends_on") or []],
                exit_criteria=[_text(c) for c in item.get("exit_criteria") or []],
            )
        )

    known = {m.id for m in milestones}
    for milestone in milestones:
        for dep in milestone.depends_on:
            if dep not in known:
                raise ConceptError(
                    f"milestone {milestone.id} depends on {dep}, "
                    f"which is not a milestone"
                )

    criteria: list[SuccessCriterion] = []
    for item in raw.get("success_criteria") or []:
        if not isinstance(item, Mapping):
            continue
        criteria.append(
            SuccessCriterion(
                id=_text(item.get("id")) or f"S{len(criteria) + 1:03d}",
                statement=_text(item.get("statement")),
                kind=_text(item.get("kind")).lower() or "measurable",
                metric=_text(item.get("metric")),
                threshold=_text(item.get("threshold")),
            )
        )

    return Brief(
        title=title,
        pitch=pitch,
        audience=_norm_list(raw.get("audience")),
        platforms=_norm_list(raw.get("platforms")),
        core_loop=_core_loop(raw.get("core_loop")),
        features=features,
        risks=risks,
        milestones=milestones,
        success_criteria=criteria,
    )


# ── contradiction detection ──────────────────────────────────────────────────


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _stem(word: str) -> str:
    for suffix in ("ing", "ies", "es", "ed", "s"):
        if len(word) > 4 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _stems(text: str) -> set[str]:
    return {_stem(w) for w in _tokens(text)}


def _has_cycle(milestones: Iterable[Milestone]) -> list[str]:
    graph = {m.id: list(m.depends_on) for m in milestones}
    state: dict[str, int] = {}

    def walk(node: str) -> bool:
        marker = state.get(node, 0)
        if marker == 1:
            return True
        if marker == 2:
            return False
        state[node] = 1
        for dep in graph.get(node, []):
            if walk(dep):
                return True
        state[node] = 2
        return False

    return [node for node in graph if walk(node)]


def detect_contradictions(brief: Brief) -> list[Contradiction]:
    """Find places where the brief argues with itself."""
    found: list[Contradiction] = []

    missing = brief.core_loop.missing()
    if missing:
        found.append(
            Contradiction(
                "incomplete_core_loop",
                "critical",
                "core loop is missing: " + ", ".join(missing),
            )
        )

    if brief.core_loop.is_complete():
        pitch_stems = _stems(brief.pitch)
        loop_stems = _stems(brief.core_loop.as_text())
        if pitch_stems and loop_stems and not (pitch_stems & loop_stems):
            found.append(
                Contradiction(
                    "pitch_loop_mismatch",
                    "high",
                    "the pitch promises "
                    f"{sorted(pitch_stems)[:4]} but the core loop delivers "
                    f"{sorted(loop_stems)[:4]}",
                )
            )

    for feature in brief.features:
        if feature.must_have and not feature.supports:
            found.append(
                Contradiction(
                    "orphan_must_have",
                    "high",
                    f"{feature.id} ({feature.name}) is must-have but supports "
                    "no part of the core loop",
                )
            )

    for risk in brief.risks:
        if risk.severity == "critical" and not risk.mitigated:
            found.append(
                Contradiction(
                    "unmitigated_critical_risk",
                    "critical",
                    f"{risk.id} is critical with no mitigation",
                )
            )

    cycle = _has_cycle(brief.milestones)
    if cycle:
        found.append(
            Contradiction(
                "milestone_cycle",
                "critical",
                "milestone dependencies form a cycle through "
                + ", ".join(cycle),
            )
        )

    has_vr = any(any(t in p for t in _VR_TOKENS) for p in brief.platforms)
    has_pc = any(any(t in p for t in _PC_TOKENS) for p in brief.platforms)
    if has_vr and has_pc:
        justified = any(
            "vr" in (r.mitigation + " " + r.description).lower()
            for r in brief.risks
        )
        if not justified:
            found.append(
                Contradiction(
                    "platform_scope_clash",
                    "high",
                    "targets both a headset and a desktop platform with no VR "
                    "justification or mitigation recorded",
                )
            )

    return found


# ── scope control ────────────────────────────────────────────────────────────


def assess_scope(brief: Brief, budget_days: float) -> list[ScopeFinding]:
    """Find commitments that do not fit inside budget_days."""
    if budget_days is None or float(budget_days) <= 0:
        raise ConceptError("budget_days must be a positive number")
    budget = float(budget_days)
    total = brief.total_effort_days
    findings: list[ScopeFinding] = []

    if total > budget:
        findings.append(
            ScopeFinding(
                "committed_exceeds_budget",
                "critical",
                f"{total:g} days are already committed against a "
                f"{budget:g} day budget",
                round(total - budget, 2),
            )
        )

    if total > budget * UNREALISTIC_MULTIPLE:
        findings.append(
            ScopeFinding(
                "plan_unrealistic",
                "high",
                f"plan is {total / budget:.1f}x the {budget:g} day budget",
                round(total - budget, 2),
            )
        )

    limit = budget * FAT_OPTIONAL_SHARE
    for feature in brief.features:
        if feature.is_optional and feature.effort_days > limit:
            findings.append(
                ScopeFinding(
                    "fat_optional_feature",
                    "medium",
                    f"{feature.id} ({feature.name}) costs "
                    f"{feature.effort_days:g} days — more than "
                    f"{FAT_OPTIONAL_SHARE:.0%} of the {budget:g} day budget",
                    float(feature.effort_days),
                )
            )

    if total > 0:
        peripheral = [f for f in brief.features if f.is_peripheral]
        peripheral_days = float(sum(f.effort_days for f in peripheral))
        share = peripheral_days / total
        if peripheral and share > PERIPHERAL_SHARE_LIMIT:
            findings.append(
                ScopeFinding(
                    "peripheral_dominates",
                    "medium",
                    f"peripheral features take {share:.0%} of all planned "
                    f"effort ({peripheral_days:g} of {total:g} days)",
                    peripheral_days,
                )
            )

    return findings


# ── success criteria ─────────────────────────────────────────────────────────


def missing_success_criteria(brief: Brief) -> list[str]:
    """Return the criterion kinds the brief does not actually define."""
    satisfied: set[str] = set()
    for criterion in brief.success_criteria:
        if criterion.is_usable and criterion.kind in CRITERIA_KINDS:
            satisfied.add(criterion.kind)
    return [kind for kind in CRITERIA_KINDS if kind not in satisfied]


# ── core-loop support ────────────────────────────────────────────────────────


def core_loop_support(brief: Brief) -> dict[str, Any]:
    """How much of the core loop the feature list actually carries."""
    coverage = {part: [] for part in CORE_PARTS}
    unsupported: list[str] = []
    supporting = 0

    for feature in brief.features:
        parts = [p for p in feature.supports if p in coverage]
        if not parts:
            unsupported.append(feature.id)
            continue
        supporting += 1
        for part in parts:
            coverage[part].append(feature.id)

    total = len(brief.features)
    return {
        "features_not_supporting_core": unsupported,
        "support_ratio": (supporting / total) if total else 0.0,
        "uncovered_core_parts": [p for p in CORE_PARTS if not coverage[p]],
        "coverage_by_core_part": coverage,
    }


# ── GDD ──────────────────────────────────────────────────────────────────────


def _verdict(contradictions, findings) -> str:
    critical = [c for c in contradictions if c.severity == "critical"]
    critical += [f for f in findings if f.severity == "critical"]
    return "BLOCKED" if critical else "READY FOR REVIEW"


def render_gdd(
    brief: Brief,
    budget_days: float,
    contradictions: list[Contradiction] | None = None,
    scope_findings: list[ScopeFinding] | None = None,
) -> str:
    """Render the controlled GDD for a brief."""
    if contradictions is None:
        contradictions = detect_contradictions(brief)
    if scope_findings is None:
        scope_findings = assess_scope(brief, budget_days)

    verdict = _verdict(contradictions, scope_findings)
    support = core_loop_support(brief)
    lines: list[str] = [f"# {brief.title}", ""]

    lines += ["## Pitch", "", brief.pitch, ""]
    lines += ["## Audience", ""]
    lines += [f"- {a}" for a in brief.audience] or ["- (none recorded)"]
    lines += ["", "## Platforms", ""]
    lines += [f"- {p}" for p in brief.platforms] or ["- (none recorded)"]

    lines += ["", "## Core Loop", ""]
    loop = brief.core_loop
    for part in CORE_PARTS:
        lines.append(f"- **{part}**: {getattr(loop, part) or '_(empty)_'}")
    if loop.duration_seconds is not None:
        lines.append(f"- **duration**: {loop.duration_seconds}s")

    lines += ["", "## Success Criteria", ""]
    if brief.success_criteria:
        lines += ["| ID | Statement | Kind | Metric | Threshold |",
                  "| --- | --- | --- | --- | --- |"]
        for c in brief.success_criteria:
            lines.append(
                f"| {c.id} | {c.statement} | {c.kind} | "
                f"{c.metric or '—'} | {c.threshold or '—'} |"
            )
    else:
        lines.append("_No success criteria recorded._")
    unset = missing_success_criteria(brief)
    if unset:
        lines += ["", f"Missing criterion kinds: {', '.join(unset)}."]

    lines += ["", "## Feature List", ""]
    lines += [
        "| ID | Feature | Supports | Effort (days) | Must-have |",
        "| --- | --- | --- | --- | --- |",
    ]
    for f in brief.features:
        lines.append(
            f"| {f.id} | {f.name} | {', '.join(f.supports) or '—'} | "
            f"{f.effort_days:g} | {'yes' if f.must_have else 'no'} |"
        )
    lines += ["", f"Total planned effort: {brief.total_effort_days:g} days "
                  f"against a {float(budget_days):g} day budget."]

    lines += ["", "## Risks", ""]
    if brief.risks:
        for r in brief.risks:
            lines.append(
                f"- **{r.id}** ({r.severity}/{r.likelihood}): "
                f"{r.description} — mitigation: "
                f"{r.mitigation or '_none_'}"
            )
    else:
        lines.append("_No risks recorded._")

    lines += ["", "## Milestones", ""]
    if brief.milestones:
        for m in brief.milestones:
            deps = f" (after {', '.join(m.depends_on)})" if m.depends_on else ""
            lines.append(f"- **{m.id}** {m.name}{deps}")
    else:
        lines.append("_No milestones recorded._")

    lines += ["", "## Control Findings", ""]
    findings = [f"{c.code} [{c.severity}]: {c.detail}" for c in contradictions]
    findings += [f"{f.code} [{f.severity}]: {f.detail}" for f in scope_findings]
    lines += [f"- {item}" for item in findings] or ["- none"]
    lines += ["", f"Support ratio: {support['support_ratio']:.0%}"]
    if support["features_not_supporting_core"]:
        lines.append(
            "Features not supporting the core loop: "
            + ", ".join(support["features_not_supporting_core"])
        )
    if support["uncovered_core_parts"]:
        lines.append(
            "Uncovered core parts: " + ", ".join(support["uncovered_core_parts"])
        )

    lines += ["", "## Sign-off", "", f"**{verdict}**"]
    return "\n".join(lines) + "\n"


# ── whole pipeline ───────────────────────────────────────────────────────────


def analyse(concept: Mapping[str, Any], budget_days: float) -> dict[str, Any]:
    """Run pipeline 1 end to end and return a serialisable report."""
    brief = build_brief(concept)
    contradictions = detect_contradictions(brief)
    findings = assess_scope(brief, budget_days)
    criteria_missing = missing_success_criteria(brief)
    support = core_loop_support(brief)
    verdict = _verdict(contradictions, findings)

    critical_count = len(
        [c for c in contradictions if c.severity == "critical"]
    ) + len([f for f in findings if f.severity == "critical"])

    return {
        "title": brief.title,
        "verdict": verdict.replace(" ", "_"),
        "budget_days": float(budget_days),
        "total_effort_days": brief.total_effort_days,
        "critical_count": critical_count,
        "contradictions": [
            {"code": c.code, "severity": c.severity, "detail": c.detail}
            for c in contradictions
        ],
        "scope_findings": [
            {
                "code": f.code,
                "severity": f.severity,
                "detail": f.detail,
                "impact_days": f.impact_days,
            }
            for f in findings
        ],
        "missing_success_criteria": criteria_missing,
        "core_loop_support": support,
        "gdd": render_gdd(brief, budget_days, contradictions, findings),
    }
