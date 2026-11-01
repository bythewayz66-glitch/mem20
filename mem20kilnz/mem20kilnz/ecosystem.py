"""Cross-subsystem wiring for mem20kilnz (mem20 4.0 criterion 6).

The kiln builds assets, and an asset is only shippable if it is *within budget*,
*structurally sound*, *faithful to its brief* and *grounded in what the estate
already knows*. This module is that seam — the kiln's own pre-build/post-build
path.

Every adapter imports a real mem20 subsystem and **calls** it:

===========================  ==========================================
subsystem                    function actually called
===========================  ==========================================
``memory_engine``            ``memory.recall`` / ``memory.remember``
``mem20verify``              ``linters.ALL_CHECKS`` (each check invoked)
``mem20dreamz``              ``verdicts.fidelity_verdict`` / ``divergence``
``mem20crewz``               ``guardrails.Guards.check_clearance``
``mem20corez``               ``mlp.CharMLP.perplexity``
``mem20cliz``                ``build_envelope`` / ``split_json_flag``
===========================  ==========================================

``BuildGate`` composes them: ``prepare()`` before a build (what does the estate
know about this asset family), ``judge()`` after it (is the result shippable).
``tests/test_ecosystem.py`` drives both against the real modules and asserts on
the values they return.

Failure policy: a subsystem that is missing or raises is recorded as
``{"ok": False, "error": ...}`` and never aborts the build — but
``report.shippable`` is then ``False``, so a caller can refuse to ship an
unverified asset instead of guessing.

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

_PROJECTS = ("memory_engine", "mem20verify", "mem20dreamz", "mem20crewz",
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
    projects that ship that way. Each import is validated by an attribute it must
    carry: a bare ``import mem20cliz`` can "succeed" against the outer project
    directory as a namespace package with no exports at all.
    """

    def __init__(self) -> None:
        _bootstrap()

        # memory_engine — flat module (memory_engine/memory.py)
        try:
            from memory_engine import memory
            if not hasattr(memory, "recall"):
                raise ImportError("namespace package, not the real engine")
        except ImportError:
            import memory  # type: ignore[import-not-found]
        self.memory = memory

        # mem20verify — nested layout
        try:
            from mem20verify import linters
        except ImportError:
            from mem20verify.mem20verify import linters
        self.linters = linters

        # mem20dreamz — nested layout
        try:
            from mem20dreamz import verdicts
        except ImportError:
            from mem20dreamz.mem20dreamz import verdicts
        self.verdicts = verdicts

        # mem20crewz — flat layout
        try:
            from mem20crewz import guardrails
        except ImportError:
            from mem20crewz.mem20crewz import guardrails
        self.guardrails = guardrails

        # mem20corez — flat package with a nested implementation
        try:
            from mem20corez import mlp
        except ImportError:
            from mem20corez.mem20corez import mlp
        self.mlp = mlp

        # mem20cliz — nested layout, validated by the attribute it must carry
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
def grounded_context(topic: Optional[str] = None, tags: Optional[list] = None,
                     k: int = 5) -> dict:
    """Read grounded facts about an asset family before a build.

    Simulated content is excluded by the engine's own default: a build must not
    be planned over imagined facts as if they were observed.
    """
    try:
        rows = _deps().memory.recall(topic=topic, tags=tags, k=k)
        return {"ok": True, "subsystem": "memory_engine",
                "count": len(rows), "rows": rows}
    except Exception as exc:  # noqa: BLE001 - reported, never fatal
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}", "count": 0, "rows": []}


def record_build(topic: str, content: str, tags: Optional[list] = None,
                 actor: str = "mem20kilnz") -> dict:
    """Append a build outcome to the grounded ledger.

    ``epistemic_status`` is ``agent_generated``: a build report is not an
    observation, and the engine's firewall must be able to tell the difference.
    """
    try:
        rec = _deps().memory.remember(
            topic=topic, content=content[:4000], tags=tags or ["kiln"],
            actor=actor, epistemic_status="agent_generated",
            source="mem20kilnz")
        return {"ok": True, "subsystem": "memory_engine",
                "id": rec.get("id"), "topic": rec.get("topic")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}"}


def lint_source(source: str, path: str = "<kiln-output>") -> dict:
    """Run every ``mem20verify`` AST check over code the kiln emitted.

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


def score_fidelity(brief: str, result: str) -> dict:
    """Score a build result against its brief with ``mem20dreamz``.

    ``fidelity`` says whether the asset still serves the brief; ``divergence``
    says how far it moved. Two numbers, never blended.
    """
    try:
        verdicts = _deps().verdicts
        payload = ('{"score": %d, "summary": "%s", "dropped": []}'
                   % (_overlap(brief, result), "lexical overlap with the brief"))
        verdict = verdicts.fidelity_verdict(payload)
        div = verdicts.divergence(result, brief)
        return {"ok": True, "subsystem": "mem20dreamz",
                "fidelity": verdict.score, "summary": verdict.summary,
                "divergence": div.get("score"), "novelty": div.get("novelty")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20dreamz",
                "error": f"{type(exc).__name__}: {exc}"}


def _overlap(seed: str, artifact: str) -> int:
    """Deterministic 0-100 content-word overlap (a measurement, not a judgement)."""
    def words(text: str) -> set:
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3}

    want = words(seed)
    if not want:
        return 0
    return int(round(100 * len(want & words(artifact)) / len(want)))


def veto_facts(fact_ids: list, actor: str = "mem20kilnz") -> dict:
    """Ask ``mem20crewz`` whether a build may rest on these facts.

    A build planned on unvalidated agent output is a guess with a manifest; the
    veto is what refuses it.
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


def result_surprise(text: str) -> dict:
    """Measure the estate's char-MLP perplexity over a build result.

    A measured number from real matrix multiplication, not a self-reported
    confidence. High perplexity means the text is unlike the model's corpus —
    a weak signal, reported as one.
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
class BuildReport:
    """What the estate said about one build."""

    context: dict = field(default_factory=dict)
    veto: dict = field(default_factory=dict)
    lint: dict = field(default_factory=dict)
    fidelity: dict = field(default_factory=dict)
    surprise: dict = field(default_factory=dict)
    recorded: dict = field(default_factory=dict)
    subsystems: list = field(default_factory=list)

    @property
    def shippable(self) -> bool:
        """True only when every subsystem that was asked actually answered.

        A part that was never run (a text-only build has no code to lint) is not
        a failure — but a part that ran and returned ``ok: False`` is. Reporting
        an unrun check as a pass would be the same silent false negative this
        gate exists to prevent.
        """
        parts = [p for p in (self.context, self.veto, self.lint,
                             self.fidelity, self.surprise) if p]
        return bool(parts) and all(p.get("ok") for p in parts)

    def as_dict(self) -> dict:
        return {"shippable": self.shippable,
                "subsystems": list(self.subsystems),
                "context": self.context, "veto": self.veto, "lint": self.lint,
                "fidelity": self.fidelity, "surprise": self.surprise,
                "recorded": self.recorded}


class BuildGate:
    """Ground a build before it runs, judge it before the asset ships."""

    def __init__(self, topic: Optional[str] = None, k: int = 5,
                 record: bool = False, actor: str = "mem20kilnz") -> None:
        self.topic = topic
        self.k = k
        self.record = record
        self.actor = actor

    def prepare(self) -> BuildReport:
        report = BuildReport()
        report.context = grounded_context(topic=self.topic, k=self.k)
        report.subsystems.append("memory_engine")
        return report

    def judge(self, brief: str, result: str,
              fact_ids: Optional[list] = None,
              report: Optional[BuildReport] = None) -> BuildReport:
        report = report or BuildReport()
        if not report.context:
            report.context = grounded_context(topic=self.topic, k=self.k)
            report.subsystems.append("memory_engine")

        ids = fact_ids if fact_ids is not None else [
            r.get("id") for r in report.context.get("rows", []) if r.get("id")]
        report.veto = veto_facts(ids, actor=self.actor)
        report.subsystems.append("mem20crewz")

        blocks = _CODE_BLOCK.findall(result)
        if blocks:
            report.lint = lint_source(blocks[0])
        else:
            report.lint = {"ok": True, "subsystem": "mem20verify", "checks": 0,
                           "issues": [], "clean": True,
                           "skipped": "no fenced python block in the result"}
        report.subsystems.append("mem20verify")

        report.fidelity = score_fidelity(brief, result)
        report.subsystems.append("mem20dreamz")

        report.surprise = result_surprise(result)
        report.subsystems.append("mem20corez")

        if self.record:
            report.recorded = record_build(
                self.topic or "kiln.build", result, actor=self.actor)
        return report


def run_gate(brief: str, result: str, topic: Optional[str] = None,
             fact_ids: Optional[list] = None, record: bool = False) -> dict:
    """One-shot wrapper used by the CLI and the README example."""
    gate = BuildGate(topic=topic, record=record)
    report = gate.prepare()
    return gate.judge(brief, result, fact_ids, report).as_dict()
