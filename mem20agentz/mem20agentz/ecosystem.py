"""Cross-subsystem wiring for mem20agentz (mem20 4.0 criterion 6).

The agent platform is not useful on its own: a run has to *read* grounded
memory before it reasons, and *check* its own answer against the estate's
verifiers before it speaks. This module is that seam.

Every adapter below imports a real mem20 subsystem and **calls** it. None of
them is a bare import kept alive for a static analyser:

===========================  ==========================================
subsystem                    function actually called
===========================  ==========================================
``memory_engine``            ``memory.recall`` / ``memory.remember``
``mem20crewz``               ``guardrails.Guards.check_clearance``
``mem20dreamz``              ``verdicts.fidelity_verdict`` / ``divergence``
``mem20verify``              ``linters.ALL_CHECKS`` (each check invoked)
``mem20kilnz``               ``budgets.check_triangles``
``mem20corez``               ``mlp.CharMLP.perplexity``
``mem20cliz``                ``split_json_flag`` / ``SCHEMA_VERSION``
===========================  ==========================================

``GroundingPipeline`` composes them into the two halves of an agent turn:
``prepare()`` before the loop (grounded context) and ``review()`` after it
(epistemic veto, fidelity, lint, budget, model-confidence). ``tests/
test_ecosystem.py`` drives both halves against the real modules and asserts on
the values they return, so the wiring is exercised, not merely declared.

Failure policy: a subsystem that is missing or raises is recorded as
``{"ok": False, "error": ...}`` in the report and never aborts the turn. An
agent that cannot reach a verifier must still answer — but the report says so,
so a caller can refuse to trust an unverified answer instead of guessing.

Import layout note
------------------
Every subsystem lives at ``<repo>/<name>/<name>/``. With the repo root on
``sys.path`` the *outer* ``<repo>/<name>`` directory matches as a namespace
package, so ``import mem20verify`` yields a module with ``__file__ is None`` and
no exports. The imports below are therefore written as
``from <name>.<name> import <module>``, which resolves the inner real package,
and ``_bootstrap()`` puts each project directory on ``sys.path`` first so the
same statement also works when the repo root is not on the path at all.
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
             "mem20kilnz", "mem20corez", "mem20cliz")


def _bootstrap() -> None:
    """Put the repo root and each subsystem project dir on ``sys.path``.

    Idempotent, and cheap enough to call at import time. The project dirs come
    first so ``import mem20cliz`` finds the real package rather than the outer
    namespace directory.
    """
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
    """Read grounded facts from ``memory_engine``.

    Simulated content is excluded by the engine's own default, which is the
    point: an agent must not reason over imagined facts as if they were
    observed.
    """
    try:
        from memory_engine import memory

        rows = memory.recall(topic=topic, tags=tags, k=k)
        return {"ok": True, "subsystem": "memory_engine",
                "count": len(rows), "rows": rows}
    except Exception as exc:  # noqa: BLE001 - reported, never fatal
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}", "count": 0, "rows": []}


def record_turn(topic: str, content: str, tags: Optional[list] = None,
                actor: str = "mem20agentz",
                epistemic_status: str = "agent_generated") -> dict:
    """Append the turn to the grounded ledger through ``memory_engine``.

    ``epistemic_status`` is required by the engine and is deliberately
    ``agent_generated``: an agent's own output is not an observation.
    """
    try:
        from memory_engine import memory

        rec = memory.remember(topic=topic, content=content, tags=tags,
                              actor=actor, epistemic_status=epistemic_status,
                              source="mem20agentz")
        return {"ok": True, "subsystem": "memory_engine",
                "id": rec.get("id"), "topic": rec.get("topic")}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "memory_engine",
                "error": f"{type(exc).__name__}: {exc}"}


def _align_store() -> None:
    """Point every subsystem's ``memory`` module at the same store.

    ``memory_engine.memory`` is the engine; the repo-root ``memory.py`` is a
    re-export shim, and ``mem20crewz``/``mem20agentz`` import the shim. Those
    are two distinct module objects, so a store redirected on one (a test, or
    ``MEM20_STORE_PATH`` set after import) leaves the other reading the default
    ``~/.mem20/store``. The veto would then answer about a different ledger than
    the one the agent just wrote to — a silent wrong answer, not an error.

    Copy the engine's path constants onto the shim so every subsystem in this
    process reads one ledger. Idempotent and cheap.
    """
    try:
        from memory_engine import memory as engine
    except Exception:  # noqa: BLE001 - nothing to align
        return

    # Every module object that could be holding its own copy of the paths: the
    # engine, the repo-root shim, and whatever module a long-lived backend
    # cached before the store moved (a backend keeps ``_mem`` for the life of
    # the process, so a stale shim there would keep reading the old ledger).
    targets = [engine]
    for mod in list(sys.modules.values()):
        if getattr(mod, "__name__", "") in ("memory", "memory_engine.memory"):
            targets.append(mod)
    try:
        from mem20crewz import _substrate as crewz_substrate

        cached = getattr(crewz_substrate.backend, "_mem", None)
        if cached is not None:
            targets.append(cached)
    except Exception:  # noqa: BLE001 - crewz not importable, nothing cached
        pass

    for target in targets:
        if target is engine:
            continue
        for attr in ("STORE_DIR", "MEM_DIR", "LEDGER", "ENTRIES", "INDEX",
                     "BACKUP_DIR", "VECTOR_INDEX", "VECTOR_META", "BM25_INDEX",
                     "BM25_CORPUS", "GRAPH_INDEX", "SIMULATED_LEDGER"):
            if hasattr(engine, attr):
                setattr(target, attr, getattr(engine, attr))


def veto_facts(fact_ids: list, actor: str = "mem20agentz") -> dict:
    """Ask ``mem20crewz``'s epistemic veto whether a plan may proceed.

    The veto is advisory here (``check_clearance``), not enforced: the agent
    reports the verdict and lets the caller decide. ``require_clearance`` is
    the enforcing variant and is what a Crew uses.
    """
    try:
        from mem20crewz import guardrails

        _align_store()
        guards = guardrails.Guards(actor=actor, enforce_plan=False,
                                   sweep_after=False)
        verdict = guards.check_clearance(list(fact_ids or []))
        # The engine's veto payload uses the key ``veto``; older callers used
        # ``vetoed``. Read both so a rename on either side cannot silently turn
        # a real veto into a pass.
        vetoed = bool(verdict.get("veto", verdict.get("vetoed", False)))
        return {"ok": True, "subsystem": "mem20crewz",
                "vetoed": vetoed,
                "reason": verdict.get("message") or verdict.get("reason", ""),
                "offenders": verdict.get("offenders", []),
                "verdict": verdict}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20crewz",
                "error": f"{type(exc).__name__}: {exc}", "vetoed": False}


def score_fidelity(seed: str, artifact: str) -> dict:
    """Score an answer against the brief with ``mem20dreamz``'s verdicts.

    Two independent numbers, never blended: ``fidelity`` (does it still serve
    the brief) and ``divergence`` (how far it moved from the reference).
    """
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
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20dreamz",
                "error": f"{type(exc).__name__}: {exc}"}


def _overlap_score(seed: str, artifact: str) -> int:
    """Deterministic 0-100 lexical overlap, used as the fidelity input.

    This is a *measurement*, not a model judgement: it is the fraction of the
    brief's content words that survive into the answer. A model-scored verdict
    needs a panel; this keeps the pipeline runnable offline and honest about
    what it measured.
    """
    def words(text: str) -> set:
        return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3}

    want = words(seed)
    if not want:
        return 0
    return int(round(100 * len(want & words(artifact)) / len(want)))


def lint_source(source: str, path: str = "<agent-output>") -> dict:
    """Run every ``mem20verify`` AST check over generated source.

    Each check in ``ALL_CHECKS`` is invoked, so a new check added to the
    verifier is picked up here without touching this module.
    """
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
    except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20kilnz",
                "error": f"{type(exc).__name__}: {exc}"}


def model_confidence(text: str) -> dict:
    """Measure the estate's own char-MLP perplexity over the answer.

    ``mem20corez`` computes this from real matrix multiplication, so it is a
    measured number rather than a self-reported confidence. High perplexity
    means the answer is unlike the model's corpus — a weak signal, reported as
    one, never as a probability of correctness.
    """
    try:
        from mem20corez import mlp

        model = mlp.CharMLP()
        return {"ok": True, "subsystem": "mem20corez",
                "perplexity": float(model.perplexity(text)),
                "params": int(model.param_count())}
    except Exception as exc:  # noqa: BLE001
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
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "subsystem": "mem20cliz",
                "error": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------
# the pipeline
# --------------------------------------------------------------------------
@dataclass
class GroundingReport:
    """What the estate said about one agent turn."""

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
        """True only when every subsystem that was asked actually answered."""
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


_CODE_BLOCK = re.compile(r"```(?:python)?\n(.*?)```", re.S)
_TRIANGLES = re.compile(r"(\d[\d,]{2,})\s*(?:triangles|tris)\b", re.I)


class GroundingPipeline:
    """Ground a prompt, then review the answer, using the wider estate.

    ``prepare`` runs before the agent loop; ``review`` runs after it. Both are
    cheap and both are exception-safe, so a broken sibling subsystem degrades
    the report instead of the run.
    """

    def __init__(self, topic: Optional[str] = None, k: int = 5,
                 record: bool = False, actor: str = "mem20agentz") -> None:
        self.topic = topic
        self.k = k
        self.record = record
        self.actor = actor

    # ------------------------------------------------------------- prepare
    def prepare(self, prompt: str) -> GroundingReport:
        report = GroundingReport()
        report.context = grounded_context(topic=self.topic, k=self.k)
        report.subsystems.append("memory_engine")
        return report

    # -------------------------------------------------------------- review
    def review(self, prompt: str, answer: str,
               report: Optional[GroundingReport] = None) -> GroundingReport:
        report = report or GroundingReport()
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
            # Nothing to lint is not a failure: report it as a clean no-op so
            # `verified` still reflects the subsystems that did run.
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
            report.recorded = record_turn(
                topic=self.topic or "mem20agentz.turn",
                content=answer[:4000],
                tags=["mem20agentz", "turn"],
                actor=self.actor)
        return report


def run_pipeline(prompt: str, answer: str, topic: Optional[str] = None,
                 k: int = 5, record: bool = False) -> dict:
    """One-shot convenience wrapper used by the CLI and the README example."""
    pipe = GroundingPipeline(topic=topic, k=k, record=record)
    report = pipe.prepare(prompt)
    return pipe.review(prompt, answer, report).as_dict()
