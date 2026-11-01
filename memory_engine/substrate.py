"""memory_engine 4.0 substrate — the stable public API other subsystems wire against.

This module is the *contract* layer. It does not re-implement retrieval; it
composes the engine (``memory_engine.memory``) with the rest of the mem20
estate so a caller gets one honest answer instead of five half-answers.

Why it exists
-------------
Before 4.0 the engine was a leaf: it stored and recalled, and every other
subsystem re-derived its own view of "is this fact trustworthy", "what does
this CLI emit", "is this subsystem even installed". That duplication is where
the estate's disagreements came from. ``substrate`` is the single place those
questions are answered, and every answer is produced by calling the owning
module — never by copying its logic.

The modules this file imports AND calls on a tested path
---------------------------------------------------------
``memory_engine.memory``  the ledger, recall, and the epistemic veto
``mem20cliz``             the fleet JSON envelope every CLI must emit
``mem20crewz``            the guardrail bundle (plan gate + epistemic clearance)
``mem20agentz``           namespace naming for per-agent memory partitions
``toolchest``             the installed-subsystem catalogue (is this real?)
``mem20dreamz``           dream lineages (a fact is only as good as its artifact)
``mem20kilnz``            glTF/GLB validation before an artifact is trusted

Public API (stable for 4.0 — see docs/renovation/4.0/SUBSTRATE.md)
------------------------------------------------------------------
``remember_fact``      write a grounded fact, refusing an undeclared basis
``recall_facts``       recall with the epistemic label intact
``veto_plan``          may a plan rest on these fact ids?
``guard_plan``         the same question through mem20crewz's guardrail bundle
``namespace_for_agent`` the memory namespace a given agent owns
``subsystem_status``   is a subsystem installed, and what does it expose?
``envelope``           wrap any CLI result in the fleet envelope
``health``             one dict describing the whole substrate
``dream_lineage``      open a dream lineage and read its current artifact
``validate_artifact``  validate a glTF/GLB artifact before it is trusted
"""

from __future__ import annotations

import os
import sys
from typing import Any, Iterable, Optional

__all__ = [
    "SubstrateError",
    "remember_fact",
    "recall_facts",
    "veto_plan",
    "guard_plan",
    "namespace_for_agent",
    "subsystem_status",
    "envelope",
    "health",
    "dream_lineage",
    "validate_artifact",
    "PUBLIC_API",
]

#: The stable 4.0 surface. Waves 2-3 wire against exactly these names.
PUBLIC_API = (
    "remember_fact",
    "recall_facts",
    "veto_plan",
    "guard_plan",
    "namespace_for_agent",
    "subsystem_status",
    "envelope",
    "health",
    "dream_lineage",
    "validate_artifact",
)

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SubstrateError(RuntimeError):
    """A substrate call could not be completed, and says why."""


def _ensure_paths() -> None:
    """Make the sibling subsystems importable without an install step.

    mem20 is source-only (it is not on PyPI), so a caller that cloned the repo
    and ran ``pip install -r requirements.txt`` has the packages on disk but not
    on ``sys.path``. Adding the repo root and the src-layout packages here keeps
    ``import memory_engine.substrate`` working from a clean clone.
    """
    # "" and "toolchest/src" hold top-level packages; "mem20agentz" and
    # "mem20crewz" are the *outer* project dirs of nested packages
    # (mem20agentz/mem20agentz/), so the outer dir is what goes on sys.path.
    for rel in ("", "toolchest/src", "mem20cliz", "mem20agentz", "mem20crewz",
                "mem20dreamz", "mem20kilnz"):
        p = os.path.join(_REPO_ROOT, rel) if rel else _REPO_ROOT
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def _engine():
    """The memory engine module (``memory_engine.memory``)."""
    _ensure_paths()
    from memory_engine import memory as engine

    return engine


# ---------------------------------------------------------------------------
# 1. write
# ---------------------------------------------------------------------------
def remember_fact(
    topic: str,
    content: str,
    *,
    epistemic_status: str,
    tags: Optional[Iterable[str]] = None,
    actor: str = "agent",
    source: str = "memory_engine.substrate",
    confidence: Optional[float] = None,
) -> dict:
    """Store a grounded fact and return the ledger record.

    ``epistemic_status`` is keyword-only and has no default on purpose: the
    engine refuses an undeclared basis, and this wrapper must not paper over
    that by inventing one. A caller that does not know says ``"unlabeled"``.
    """
    if not topic or not content:
        raise SubstrateError("remember_fact needs a non-empty topic and content")
    engine = _engine()
    return engine.remember(
        topic=topic,
        content=content,
        tags=list(tags or []),
        actor=actor,
        epistemic_status=epistemic_status,
        source=source,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# 2. read
# ---------------------------------------------------------------------------
def recall_facts(
    topic: Optional[str] = None,
    *,
    tags: Optional[Iterable[str]] = None,
    k: int = 5,
    include_simulated: bool = False,
) -> list[dict]:
    """Recall facts, keeping the epistemic label on every row.

    A row whose label is missing is normalised to ``"unlabeled"`` rather than
    left absent: an absent label reads as "no doubt recorded", which is the
    opposite of what it means.
    """
    engine = _engine()
    rows = engine.recall(
        topic=topic,
        tags=list(tags or []) or None,
        k=k,
        include_simulated=include_simulated,
    )
    unlabeled = getattr(engine, "UNLABELED", "unlabeled")
    for r in rows:
        if isinstance(r, dict) and not r.get("epistemic_status"):
            r["epistemic_status"] = unlabeled
    return rows


# ---------------------------------------------------------------------------
# 3. trust
# ---------------------------------------------------------------------------
def veto_plan(fact_ids: Iterable[str], *, actor: str = "agent") -> dict:
    """Ask the engine whether a plan may rest on these fact ids.

    Returns the engine's own verdict dict. An id that resolves to nothing is
    reported as unresolved by the engine, not silently dropped here.
    """
    engine = _engine()
    return engine.epistemic_veto(list(fact_ids), actor=actor)


def guard_plan(fact_ids: Iterable[str], *, actor: str = "agent") -> dict:
    """The same question, asked through mem20crewz's guardrail bundle.

    mem20crewz owns the plan-execution gate and the epistemic clearance check;
    routing through it means a crew and a direct caller cannot disagree about
    whether a plan is allowed to run.
    """
    _ensure_paths()
    try:
        from mem20crewz import Guards
        from mem20crewz import _substrate as crewz_substrate
    except ImportError as exc:  # pragma: no cover - only on a broken install
        raise SubstrateError(f"mem20crewz is not importable: {exc}") from exc

    # mem20crewz resolves the engine through its module-level backend singleton
    # (``backend._mem``), which it caches on first use. That cache can hold a
    # *different module object* than the one this substrate writes through --
    # e.g. the repo-root ``memory`` shim, or a stale engine after a reload --
    # and then the guardrail would answer about a store the caller never wrote
    # to and report "OK" about facts it never saw. Bind the backend to the exact
    # engine module in use so both sides read the same ledger.
    crewz_substrate.backend._mem = _engine()

    ids = list(fact_ids)
    guards = Guards(actor=actor)
    clearance = guards.check_clearance(ids)
    blocked = False
    reason = ""
    try:
        guards.gate(ids)
    except Exception as exc:  # GuardrailBlocked, or a sealed backend
        blocked = True
        reason = str(exc)
    return {
        "blocked": blocked,
        "reason": reason,
        "clearance": clearance,
        "events": guards.events,
    }


# ---------------------------------------------------------------------------
# 4. partitioning
# ---------------------------------------------------------------------------
def namespace_for_agent(name: str) -> str:
    """The memory namespace an agent owns.

    mem20agentz owns the naming rule; this delegates so a namespace written by
    the agent platform and one written by a direct caller are the same string.
    """
    _ensure_paths()
    try:
        from mem20agentz.profiles import namespace_for
    except ImportError as exc:  # pragma: no cover
        raise SubstrateError(f"mem20agentz is not importable: {exc}") from exc
    if not name or not name.strip():
        raise SubstrateError("namespace_for_agent needs a non-empty agent name")
    return namespace_for(name)


# ---------------------------------------------------------------------------
# 5. estate introspection
# ---------------------------------------------------------------------------
def subsystem_status(name: str) -> dict:
    """Is ``name`` a real, installed mem20 subsystem, and what does it expose?

    Answered by toolchest's catalogue, which reads the pyproject and the
    import spec off disk. This is deliberately not a hardcoded list: a
    subsystem that was renamed or removed must show up as missing.
    """
    _ensure_paths()
    try:
        from toolchest import catalog
    except ImportError as exc:  # pragma: no cover
        raise SubstrateError(f"toolchest is not importable: {exc}") from exc

    # toolchest reads the estate root from MEM20_ROOT (default /opt/mem20). On a
    # source-only clone the root is wherever the repo was cloned, so point it at
    # this file's repo root unless the operator already set it.
    os.environ.setdefault("MEM20_ROOT", _REPO_ROOT)
    if str(catalog.MEM20_ROOT) != _REPO_ROOT:
        catalog.MEM20_ROOT = __import__("pathlib").Path(_REPO_ROOT)
        catalog.MCP_DIR = catalog.MEM20_ROOT / "mcp"

    inventory = catalog.build_inventory(help_sampling=False)
    for entry in inventory.get("entries", []):
        if entry.get("name") == name:
            return {
                "name": name,
                "found": True,
                "kind": entry.get("kind"),
                "category": entry.get("category"),
                "runtime_status": entry.get("runtime_status"),
                "description": entry.get("description"),
            }
    return {"name": name, "found": False, "kind": None, "category": None,
            "runtime_status": "absent", "description": None}


# ---------------------------------------------------------------------------
# 6. CLI envelope
# ---------------------------------------------------------------------------
def envelope(command: str, argv: list[str], exit_code: int,
             stdout: str = "", stderr: str = "",
             extra: Optional[dict] = None) -> dict:
    """Wrap a CLI result in the fleet envelope (mem20cliz owns the schema)."""
    _ensure_paths()
    try:
        from mem20cliz import build_envelope
    except ImportError as exc:  # pragma: no cover
        raise SubstrateError(f"mem20cliz is not importable: {exc}") from exc
    return build_envelope(command, argv, exit_code, stdout, stderr, extra)


# ---------------------------------------------------------------------------
# 7. artifacts — a fact is only as good as the artifact it points at
# ---------------------------------------------------------------------------
def dream_lineage(seed: str, *, kind: str = "active") -> dict:
    """Open a dream lineage for ``seed`` and report where it actually is.

    mem20dreamz owns the lineage; this returns its identity and current
    artifact so a caller can attach a fact to a real, resumable artifact
    instead of a string it made up.
    """
    _ensure_paths()
    try:
        from mem20dreamz import engine as dream_engine
    except ImportError as exc:  # pragma: no cover
        raise SubstrateError(f"mem20dreamz is not importable: {exc}") from exc
    if not seed or not seed.strip():
        raise SubstrateError("dream_lineage needs a non-empty seed")
    lineage = dream_engine.new_dream(seed, kind=kind)
    return {
        "dream_id": lineage.dream_id,
        "seed": lineage.seed,
        "kind": lineage.kind,
        "artifact": lineage.current_artifact(),
        "state_path": lineage.state_path,
    }


def validate_artifact(path: str) -> dict:
    """Validate a glTF/GLB artifact before anything is allowed to trust it.

    mem20kilnz owns the validator. A missing file is reported as ``ok: False``
    with a ``not_found`` finding — never as a pass.
    """
    _ensure_paths()
    try:
        # ``mem20kilnz.validate`` is a *module*; the callable lives inside it.
        from mem20kilnz.validate import validate as kilnz_validate
    except ImportError as exc:  # pragma: no cover
        raise SubstrateError(f"mem20kilnz is not importable: {exc}") from exc
    report = kilnz_validate(path)
    return {
        "path": report.path,
        "ok": bool(report.ok),
        "nodes": report.nodes,
        "findings": [
            {"severity": f.severity, "code": f.code, "message": f.message}
            for f in report.findings
        ],
    }


# ---------------------------------------------------------------------------
# 8. health
# ---------------------------------------------------------------------------
def health() -> dict:
    """One dict describing the substrate, with every figure measured."""
    engine = _engine()
    recs = engine._load_ledger()
    remembers = [r for r in recs if r.get("action") == "remember"]
    labeled = [r for r in remembers if r.get("epistemic_status")]
    return {
        "store": getattr(engine, "STORE_DIR", None),
        "ledger_events": len(recs),
        "grounded_facts": len(remembers),
        "labeled_facts": len(labeled),
        "label_coverage": round(len(labeled) / len(remembers), 4) if remembers else 1.0,
        "vector_available": bool(getattr(engine, "VECTOR_AVAILABLE", False)),
        "bm25_available": bool(getattr(engine, "BM25_AVAILABLE", False)),
        "public_api": list(PUBLIC_API),
    }
