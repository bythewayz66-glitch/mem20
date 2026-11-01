"""Cross-subsystem wiring for mem20dreamz (mem20 4.0 criterion 6).

A dream is only worth keeping if it is *new* and *true*. The dream engine
already measures novelty against its own lineage; this module adds the estate's
other half — grounding, epistemic veto, structural lint, asset budget and a
corpus-distance measure — so a candidate that invents a fact, ships broken code
or blows a triangle budget is caught before it is promoted.

Every adapter imports a real mem20 subsystem and **calls** it:

===========================  ==========================================
subsystem                    function actually called
===========================  ==========================================
``memory_engine``            ``memory.recall`` / ``memory.remember``
``mem20crewz``               ``guardrails.Guards.check_clearance``
``mem20verify``              ``linters.ALL_CHECKS`` (each check invoked)
``mem20kilnz``               ``budgets.check_triangles``
``mem20corez``               ``mlp.CharMLP.perplexity``
``mem20cliz``                ``build_envelope`` / ``split_json_flag``
===========================  ==========================================

``DreamGate`` is the promotion gate: ``ground()`` before a dream runs (what does
the estate already know about this seed), ``judge()`` after it (is the candidate
safe to promote). ``tests/test_ecosystem.py`` drives both against the real
modules and asserts on the values they return.

Failure policy: a subsystem that is missing or raises is recorded as
``{"ok": False, "error": ...}`` and never aborts the dream — but
``report.promotable`` is then ``False``, so a caller can refuse to promote an
unverified candidate instead of guessing.

Import layout note
------------------
The estate is not uniform: some projects are a package at the project root
(``mem20crewz/guardrails.py``) and others nest it one level down
(``mem20verify/mem20verify/linters.py``). ``_Deps`` tries the flat layout first
and falls back to the nested one, and ``_bootstrap`` puts the project
directories ahead of the repo root so the real package wins over the outer
directory that would otherwise match as a namespace package.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

_PROJECTS = ("memory_engine", "mem20crewz", "mem20verify", "mem20kilnz",
             "mem20corez", "mem20cliz")


def _bootstrap() -> None:
    """Put each subsystem project dir ahead of the repo root on ``sys.path``."""
    for name in reversed(_PROJECTS):
        path = str(_REPO_ROOT / name)
        if path in sys.path:
            sys.path.remove(path)
        sys.path.insert(0, path)
    root = str(_REPO_ROOT)
    if root in sys.path:
        sys.path.remove(root)
    sys.path.append(root)


_bootstrap()


class _Deps:
    """The sibling subsystems, imported once and held.

    The imports are written out literally so the dependency is visible to a
    reader and to the conformance scanner, with a nested-layout fallback for the
    projects that ship that way.
    """

    def __init__(self) -> None:
        _bootstrap()

        # memory_engine — flat module (memory_engine/memory.py)
        try:
            from memory_engine import memory
        except ImportError:
            import memory  # type: ignore[import-not-found]
        self.memory = memory

        # mem20crewz — flat layout
        try:
            from mem20crewz import guardrails
        except ImportError:
            from mem20crewz.mem20crewz import guardrails
        self.guardrails = guardrails

        # mem20verify — nested layout
        try:
            from mem20verify import linters
        except ImportError:
            from mem20verify.mem20verify import linters
        self.linters = linters

        # mem20kilnz — nested layout
        try:
            from mem20kilnz import budgets
        except ImportError:
            from mem20kilnz.mem20kilnz import budgets
        self.budgets = budgets

        # mem20corez — flat package with a nested implementation
        try:
            from mem20corez import mlp
        except ImportError:
            from mem20corez.mem20corez import mlp
        self.mlp = mlp

        # mem20cliz — nested layout. A bare ``import mem20cliz`` can succeed
        # against the outer directory as a namespace package (no exports), so
        # the import is validated by the attribute it must carry.
        try:
            import mem20cliz
            if not hasattr(mem20cliz, "split_json_flag"):
                raise ImportError("namespace package, not the real mem20cliz")
        except ImportError:
            from mem20cliz import mem20cliz
        self.cliz = mem20cliz


_DEPS: Optional[_Deps] = None


def _deps() -> _Deps:
    """Lazily build the dependency bundle (import cost paid once)."""
    global _DEPS
    if _DEPS is None:
        _DEPS = _Deps()
    return _DEPS


# --------------------------------------------------------------------------
# adapters
# --------------------------------------------------------------------------
def ground_seed(seed: str, k: int = 5) -> dict:
    """Read what the estate already knows about a seed from ``memory_engine``.

    A dreamer that does not know what exists reinvents the tool sitting two
    directories away. This is the read that stops it, and it excludes simulated
    content by the engine's own default.
    """
    try:
        rows = _deps().memory.recall(topic=seed, k=k)
        return {"ok": True, "subsystem": "memory_engine",
                "count": len(rows), "rows": rows}
    except Exception as exc:  # noqa: BLE001 - reported, never fatal
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}", "count": 0, "rows": []}


def record_dream(seed: str, candidate: str, tags: Optional[list] = None,
                 actor: str = "mem20dreamz") -> dict:
    """Append the dream outcome to the grounded ledger.

    ``epistemic_status`` is ``agent_generated``: a dream is not an observation,
    and the engine's firewall must be able to tell the difference.
    """
    try:
        rec = _deps().memory.remember(
            topic=f"dream.{seed}", content=candidate[:4000],
            tags=tags or ["dream"], actor=actor,
            epistemic_status="agent_generated", source="mem20dreamz")
        return {"ok": True, "subsystem": "memory_engine",
                "id": rec.get("id"), "topic": rec.get("topic")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}"}


def veto_claims(fact_ids: list, actor: str = "mem20dreamz") -> dict:
    """Ask ``mem20crewz`` whether a dream may rest on these facts.

    A dream built on unvalidated agent output is a hallucination with a
    lineage; the veto is what refuses it.
    """
    try:
        guards = _deps().guardrails.Guards(actor=actor, enforce_plan=False,
                                           sweep_after=False)
        verdict = guards.check_clearance(list(fact_ids or []))
        vetoed = bool(verdict.get("veto", verdict.get("vetoed", False)))
        return {"ok": True, "subsystem": "mem20crewz", "vetoed": vetoed,
                "reason": verdict.get("message") or verdict.get("reason", ""),
                "offenders": verdict.get("offenders", []), "verdict": verdict}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20crewz",
                "error": f"{type(exc).__name__}: {exc}", "vetoed": False}


def lint_candidate(source: str, path: str = "<dream-candidate>") -> dict:
    """Run every ``mem20verify`` AST check over code a dream produced.

    Each check in ``ALL_CHECKS`` is invoked, so a new check added to the
    verifier is picked up here without touching this module.
    """
    try:
        linters = _deps().linters
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
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20verify",
                "error": f"{type(exc).__name__}: {exc}", "clean": False,
                "issues": []}


def check_asset_budget(family: str, triangles: int, lod: int = 0,
                       tier: str = "standard") -> dict:
    """Check a triangle count a dream proposed against ``mem20kilnz``'s table."""
    try:
        verdict = _deps().budgets.check_triangles(family, triangles, lod=lod,
                                                  tier=tier)
        return {"ok": True, "subsystem": "mem20kilnz",
                "within_budget": bool(verdict.ok), "reason": verdict.reason,
                "band": [verdict.lod0_min, verdict.lod0_max]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20kilnz",
                "error": f"{type(exc).__name__}: {exc}"}


def corpus_distance(text: str) -> dict:
    """Measure the estate's char-MLP perplexity over a candidate.

    A measured number from real matrix multiplication, not a self-reported
    novelty score. High perplexity means the text is unlike the model's corpus —
    a weak signal for novelty, reported as one, never as a quality claim.
    """
    try:
        model = _deps().mlp.CharMLP()
        return {"ok": True, "subsystem": "mem20corez",
                "perplexity": float(model.perplexity(text)),
                "params": int(model.param_count())}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20corez",
                "error": f"{type(exc).__name__}: {exc}"}


def cli_envelope(command: str, argv: list, exit_code: int, stdout: str = "",
                 stderr: str = "", extra: Optional[dict] = None) -> dict:
    """Build the fleet's shared ``--json`` envelope with ``mem20cliz``."""
    try:
        cliz = _deps().cliz
        wants_json, rest = cliz.split_json_flag(list(argv))
        env = cliz.build_envelope(command, rest, exit_code, stdout, stderr,
                                  extra)
        return {"ok": True, "subsystem": "mem20cliz", "json": wants_json,
                "envelope": env, "schema_version": cliz.SCHEMA_VERSION}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20cliz",
                "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------
# the gate
# --------------------------------------------------------------------------
_CODE_BLOCK = re.compile(r"```(?:python)?\n(.*?)```", re.S)
_TRIANGLES = re.compile(r"(\d[\d,]{2,})\s*(?:triangles|tris)\b", re.I)


@dataclass
class DreamReport:
    """What the estate said about one dream."""

    grounding: dict = field(default_factory=dict)
    veto: dict = field(default_factory=dict)
    lint: dict = field(default_factory=dict)
    budget: dict = field(default_factory=dict)
    distance: dict = field(default_factory=dict)
    recorded: dict = field(default_factory=dict)
    subsystems: list = field(default_factory=list)

    @property
    def promotable(self) -> bool:
        """True only when every subsystem that was asked actually answered.

        A part that was never run (a text-only dream has no code to lint) is not
        a failure — but a part that ran and returned ``ok: False`` is. Reporting
        an unrun check as a pass would be the same silent false negative this
        gate exists to prevent.
        """
        parts = [p for p in (self.grounding, self.veto, self.lint,
                             self.budget, self.distance) if p]
        return bool(parts) and all(p.get("ok") for p in parts)

    def as_dict(self) -> dict:
        return {"promotable": self.promotable,
                "subsystems": list(self.subsystems),
                "grounding": self.grounding, "veto": self.veto,
                "lint": self.lint, "budget": self.budget,
                "distance": self.distance, "recorded": self.recorded}


class DreamGate:
    """Ground a dream before it runs, judge it before it is promoted."""

    def __init__(self, seed: str, k: int = 5, record: bool = False,
                 actor: str = "mem20dreamz") -> None:
        self.seed = seed
        self.k = k
        self.record = record
        self.actor = actor

    def ground(self) -> DreamReport:
        report = DreamReport()
        report.grounding = ground_seed(self.seed, k=self.k)
        report.subsystems.append("memory_engine")
        return report

    def judge(self, candidate: str, fact_ids: Optional[list] = None,
              triangles: Optional[int] = None,
              report: Optional[DreamReport] = None) -> DreamReport:
        report = report or DreamReport()
        if not report.grounding:
            report.grounding = ground_seed(self.seed, k=self.k)
            report.subsystems.append("memory_engine")

        ids = fact_ids if fact_ids is not None else [
            r.get("id") for r in report.grounding.get("rows", []) if r.get("id")]
        report.veto = veto_claims(ids, actor=self.actor)
        report.subsystems.append("mem20crewz")

        blocks = _CODE_BLOCK.findall(candidate)
        if blocks:
            report.lint = lint_candidate(blocks[0])
        else:
            report.lint = {"ok": True, "subsystem": "mem20verify", "checks": 0,
                           "issues": [], "clean": True,
                           "skipped": "no fenced python block in the candidate"}
        report.subsystems.append("mem20verify")

        tri = _TRIANGLES.search(candidate)
        if triangles is not None or tri:
            count = triangles if triangles is not None else int(
                tri.group(1).replace(",", ""))
            report.budget = check_asset_budget("prop", count)
            report.subsystems.append("mem20kilnz")

        report.distance = corpus_distance(candidate)
        report.subsystems.append("mem20corez")

        if self.record:
            report.recorded = record_dream(self.seed, candidate,
                                           actor=self.actor)
        return report


def run_gate(seed: str, candidate: str, fact_ids: Optional[list] = None,
             triangles: Optional[int] = None, record: bool = False) -> dict:
    """One-shot wrapper used by the CLI and the README example."""
    gate = DreamGate(seed=seed, record=record)
    report = gate.ground()
    return gate.judge(candidate, fact_ids, triangles, report).as_dict()
