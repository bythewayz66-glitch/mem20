"""Cross-subsystem wiring for mem20teamz (mem20 4.0 criterion 6).

A team management system is not useful on its own: it needs grounded data about
team members' capabilities (from memory_engine, HR systems), must verify its
recommendations against the estate's verifiers, and must respect budget and
fidelity constraints from the wider estate.

This module is that seam. Every adapter below imports a real mem20 subsystem
and **calls** it.

===========================  ==========================================
subsystem                    function actually called
===========================  ==========================================
``memory_engine``            ``memory.recall`` / ``memory.remember``
``mem20crewz``               ``guardrails.Guards.check_clearance``
``mem20verify``              ``linters.ALL_CHECKS`` (each check invoked)
``mem20dreamz``              ``verdicts.fidelity_verdict`` / ``divergence``
``mem20kilnz``               ``budgets.check_triangles``
``mem20corez``               ``mlp.CharMLP.perplexity``
``mem20cliz``                ``split_json_flag`` / ``SCHEMA_VERSION``
``mem20gapz`` ``family_capability_gap_mapper`` / ``ecosystem.probe``
===========================  ==========================================

``TeamGovernor`` composes them into the two halves of a team operation:
``prepare()`` before the operation (grounded context from memory) and ``judge()``
after it (epistemic veto, fidelity, lint, budget, model-confidence).
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

# --------------------------------------------------------------------------
# path bootstrap — the sibling subsystems must resolve from any cwd
# --------------------------------------------------------------------------
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

#: Project directories that must be importable for the adapters below.
_PROJECTS = ("memory_engine", "mem20crewz", "mem20dreamz", "mem20verify",
             "mem20kilnz", "mem20corez", "mem20cliz", "mem20gapz")


def _bootstrap() -> None:
    """Put the repo root and each subsystem project dir on ``sys.path``."""
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path not in sys.path:
            sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


_bootstrap()


# --------------------------------------------------------------------------
# adapters — one per subsystem, each returning the subsystem's own value
# --------------------------------------------------------------------------
def grounded_context(topic: Optional[str] = None, tags: Optional[list] = None,
                     k: int = 5) -> dict:
    """Read grounded facts from ``memory_engine``."""
    try:
        from memory_engine import memory

        rows = memory.recall(topic=topic, tags=tags, k=k)
        return {"ok": True, "subsystem": "memory_engine",
                "count": len(rows), "rows": rows}
    except Exception as exc:
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}", "count": 0, "rows": []}


def record_team_outcome(topic: str, content: str, tags: Optional[list] = None,
                        actor: str = "mem20teamz",
                        epistemic_status: str = "agent_generated") -> dict:
    """Append a team outcome to the grounded ledger."""
    try:
        from memory_engine import memory

        rec = memory.remember(topic=topic, content=content, tags=tags,
                              actor=actor, epistemic_status=epistemic_status,
                              source="mem20teamz")
        return {"ok": True, "subsystem": "memory_engine",
                "id": rec.get("id"), "topic": rec.get("topic")}
    except Exception as exc:
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}"}


def _align_store() -> None:
    """Point every subsystem's ``memory`` module at the same store."""
    try:
        from memory_engine import memory as engine
    except Exception:
        return

    targets = [engine]
    for mod in list(sys.modules.values()):
        if getattr(mod, "__name__", "") in ("memory", "memory_engine.memory"):
            targets.append(mod)
    try:
        from mem20crewz import _substrate as crewz_substrate
        cached = getattr(crewz_substrate.backend, "_mem", None)
        if cached is not None:
            targets.append(cached)
    except Exception:
        pass

    for target in targets:
        if target is engine:
            continue
        for attr in ("STORE_DIR", "MEM_DIR", "LEDGER", "ENTRIES", "INDEX",
                     "BACKUP_DIR", "VECTOR_INDEX", "VECTOR_META", "BM25_INDEX",
                     "BM25_CORPUS", "GRAPH_INDEX", "SIMULATED_LEDGER"):
            if hasattr(engine, attr):
                setattr(target, attr, getattr(engine, attr))


def veto_facts(fact_ids: list, actor: str = "mem20teamz") -> dict:
    """Ask ``mem20crewz``'s epistemic veto whether a team plan may proceed."""
    try:
        from mem20crewz import guardrails

        _align_store()
        guards = guardrails.Guards(actor=actor, enforce_plan=False,
                                   sweep_after=False)
        verdict = guards.check_clearance(list(fact_ids or []))
        vetoed = bool(verdict.get("veto", verdict.get("vetoed", False)))
        return {"ok": True, "subsystem": "mem20crewz",
                "vetoed": vetoed,
                "reason": verdict.get("message") or verdict.get("reason", ""),
                "offenders": verdict.get("offenders", []),
                "verdict": verdict}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20crewz",
                "error": f"{type(exc).__name__}: {exc}", "vetoed": False}


def score_fidelity(seed: str, artifact: str) -> dict:
    """Score a team output against the brief with ``mem20dreamz``'s verdicts."""
    try:
        from mem20dreamz import verdicts

        payload = ('{"score": %d, "summary": "%s", "dropped": []}'
                   % (_overlap_score(seed, artifact),
                      "lexical overlap with the brief"))
        verdict = verdicts.fidelity_verdict(payload)
        div = verdicts.divergence(artifact, seed)
        return {"ok": True, "subsystem": "mem20dreamz",
                "fidelity": verdict.score, "summary": verdict.summary,
                "divergence": div.get("score"), "novelty": div.get("novelty")}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20dreamz",
                "error": f"{type(exc).__name__}: {exc}"}


def _overlap_score(seed: str, artifact: str) -> int:
    """Deterministic 0-100 lexical overlap."""
    def words(text: str) -> set:
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3}

    want = words(seed)
    if not want:
        return 0
    return int(round(100 * len(want & words(artifact)) / len(want)))


def lint_source(source: str, path: str = "<team-output>") -> dict:
    """Run every ``mem20verify`` AST check over generated source."""
    try:
        from mem20verify import linters

        tree = ast.parse(source)
        issues = []
        for check in linters.ALL_CHECKS:
            issues.extend(check(path, tree))
        return {"ok": True, "subsystem": "mem20verify",
                "checks": len(linters.ALL_CHECKS),
                "issues": [i.as_dict() for i in issues],
                "clean": not issues}
    except SyntaxError as exc:
        return {"ok": False, "subsystem": "mem20verify",
                "error": f"SyntaxError: {exc}", "clean": False, "issues": []}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20verify",
                "error": f"{type(exc).__name__}: {exc}", "clean": False,
                "issues": []}


def check_asset_budget(family: str, triangles: int, lod: int = 0,
                       tier: str = "standard") -> dict:
    """Check a triangle count against ``mem20kilnz``'s authored budgets."""
    try:
        from mem20kilnz import budgets

        verdict = budgets.check_triangles(family, triangles, lod=lod, tier=tier)
        return {"ok": True, "subsystem": "mem20kilnz",
                "within_budget": bool(verdict.ok), "reason": verdict.reason,
                "band": [verdict.lod0_min, verdict.lod0_max]}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20kilnz",
                "error": f"{type(exc).__name__}: {exc}"}


def model_confidence(text: str) -> dict:
    """Measure the estate's own char-MLP perplexity over the team output."""
    try:
        from mem20corez import mlp

        model = mlp.CharMLP()
        return {"ok": True, "subsystem": "mem20corez",
                "perplexity": float(model.perplexity(text)),
                "params": int(model.param_count())}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20corez",
                "error": f"{type(exc).__name__}: {exc}"}


def json_contract(argv: list) -> dict:
    """Use ``mem20cliz``'s shared machine contract for the CLI envelope."""
    try:
        import mem20cliz

        wants_json, rest = mem20cliz.split_json_flag(list(argv))
        return {"ok": True, "subsystem": "mem20cliz",
                "json": wants_json, "argv": rest,
                "schema_version": mem20cliz.SCHEMA_VERSION}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20cliz",
                "error": f"{type(exc).__name__}: {exc}"}


def capability_gap_mapper_analyze(team_skills: dict = None,
                                   role_requirements: dict = None) -> dict:
    """Run a capability gap analysis for team composition planning."""
    try:
        from mem20gapz import family_capability_gap_mapper

        request = {
            "current_capabilities": team_skills.get("current_capabilities", []) if team_skills else [],
            "required_capabilities": role_requirements.get("required_capabilities", []) if role_requirements else [],
            "context": role_requirements.get("context", {}) if role_requirements else {},
        }
        result = family_capability_gap_mapper(206, request)
        return {"ok": True, "subsystem": "mem20gapz",
                "gaps": result.get("gaps", []),
                "actions": result.get("actions", []),
                "summary": result.get("summary", {})}
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20gapz",
                "error": f"{type(exc).__name__}: {exc}"}


def capability_gap_mapper_probe() -> dict:
    """Probe the capability gap mapper subsystem."""
    try:
        from mem20gapz.ecosystem import probe as cgm_probe
        return cgm_probe(include_member_ecosystems=False)
    except Exception as exc:
        return {"ok": False, "subsystem": "mem20gapz",
                "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------
# the governor
# --------------------------------------------------------------------------
_CODE_BLOCK = re.compile(r"```(?:python)?\n(.*?)```", re.S)
_TRIANGLES = re.compile(r"(\d[\d,]{2,})\s*(?:triangles|tris)\b", re.I)


@dataclass
class TeamReport:
    """What the estate said about one team operation."""

    context: dict = field(default_factory=dict)
    veto: dict = field(default_factory=dict)
    fidelity: dict = field(default_factory=dict)
    lint: dict = field(default_factory=dict)
    budget: dict = field(default_factory=dict)
    confidence: dict = field(default_factory=dict)
    recorded: dict = field(default_factory=dict)
    subsystems: list = field(default_factory=list)

    @property
    def verified(self) -> bool:
        parts = [self.context, self.veto, self.fidelity, self.lint,
                 self.confidence]
        return all(p.get("ok") for p in parts)

    def as_dict(self) -> dict:
        return {
            "verified": self.verified,
            "subsystems": list(self.subsystems),
            "context": self.context,
            "veto": self.veto,
            "fidelity": self.fidelity,
            "lint": self.lint,
            "budget": self.budget,
            "confidence": self.confidence,
            "recorded": self.recorded,
        }


class TeamGovernor:
    """Ground a team operation before it runs, judge it before it ships."""

    def __init__(self, topic: Optional[str] = None, k: int = 5,
                 record: bool = False, actor: str = "mem20teamz") -> None:
        self.topic = topic
        self.k = k
        self.record = record
        self.actor = actor

    def prepare(self, prompt: str = "") -> TeamReport:
        report = TeamReport()
        report.context = grounded_context(topic=self.topic, k=self.k)
        report.subsystems.append("memory_engine")
        return report

    def judge(self, prompt: str, answer: str,
              report: Optional[TeamReport] = None) -> TeamReport:
        report = report or TeamReport()
        fact_ids = [r.get("id") for r in report.context.get("rows", [])
                    if r.get("id")]

        report.veto = veto_facts(fact_ids, actor=self.actor)
        report.subsystems.append("mem20crewz")

        report.fidelity = score_fidelity(prompt, answer)
        report.subsystems.append("mem20dreamz")

        blocks = _CODE_BLOCK.findall(answer)
        if blocks:
            report.lint = lint_source(blocks[0])
        else:
            report.lint = {"ok": True, "subsystem": "mem20verify",
                           "checks": 0, "issues": [], "clean": True,
                           "skipped": "no fenced python block in the answer"}
        report.subsystems.append("mem20verify")

        tri = _TRIANGLES.search(answer)
        if tri:
            report.budget = check_asset_budget(
                "prop", int(tri.group(1).replace(",", "")))
            report.subsystems.append("mem20kilnz")

        report.confidence = model_confidence(answer)
        report.subsystems.append("mem20corez")

        if self.record:
            report.recorded = record_team_outcome(
                topic=self.topic or "mem20teamz.operation",
                content=answer[:4000],
                tags=["mem20teamz", "operation"],
                actor=self.actor)
        return report


def run_governor(prompt: str, answer: str, topic: Optional[str] = None,
                 k: int = 5, record: bool = False) -> dict:
    """One-shot convenience wrapper."""
    gov = TeamGovernor(topic=topic, k=k, record=record)
    report = gov.prepare(prompt)
    return gov.judge(prompt, answer, report).as_dict()


# --------------------------------------------------------------------------
# peer probe surface
# --------------------------------------------------------------------------


def _safe_peer(name, fn):
    try:
        r = fn()
        if isinstance(r, dict):
            return {'subsystem': name, **r} if 'subsystem' not in r else r
        return {'ok': True, 'subsystem': name, 'result': r}
    except Exception as e:
        return {'ok': False, 'subsystem': name, 'error': f"{type(e).__name__}: {e}"}


def probe(include_member_ecosystems: bool = True) -> dict:
    """Probe core cross-subsystem peers."""
    core_checks = {
        'memory_engine': _safe_peer('memory_engine', lambda: grounded_context(topic='teamz-probe', k=1)),
        'mem20crewz': _safe_peer('mem20crewz', lambda: veto_facts([], actor='teamz-probe')),
        'mem20dreamz': _safe_peer('mem20dreamz', lambda: score_fidelity('probe', 'probe answer')),
        'mem20verify': _safe_peer('mem20verify', lambda: lint_source('x = 1\n')),
        'mem20kilnz': _safe_peer('mem20kilnz', lambda: check_asset_budget('probe', 100)),
        'mem20corez': _safe_peer('mem20corez', lambda: model_confidence('probe confidence text')),
        'mem20cliz': _safe_peer('mem20cliz', lambda: json_contract(['--json'])),
        'mem20gapz': _safe_peer('mem20gapz', capability_gap_mapper_probe),
    }
    reachable = [k for k, v in core_checks.items() if v.get('ok')]
    result = {
        'ok': len(reachable) >= 7,
        'count': len(reachable),
        'core_count': len(core_checks),
        'reachable': reachable,
        'checks': core_checks,
    }
    if include_member_ecosystems:
        try:
            from mem20agentz.ecosystem import _absorbed_member_peers
            amp = _absorbed_member_peers()
            result['member_ecosystems'] = amp
            result['peer_surface_total'] = int(result['core_count']) + int(amp.get('peer_checks_total', 0))
            result['count'] = result['peer_surface_total']
        except Exception:
            result['member_ecosystems'] = {'ok': True, 'members_with_ecosystem_probe': 0, 'members_ok': 0, 'peer_checks_total': 0, 'checks': {}}
            result['peer_surface_total'] = result['core_count']
            result['count'] = result['peer_surface_total']
    return result