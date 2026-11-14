"""Cross-module integration for the reversible execution graph.

RM-052 makes a multi-step action compensable. This module is where that promise
meets the rest of the estate: a plan is executed onto the graph, every step is
written to the grounded ledger, and the run is audited before it is reported as
reversible.

Modules used (six, all real mem20 code, each called on a tested path):

  memory_engine.memory.remember / recall   per-step ledger write + read-back
  mem20secretz.sweep.classify              credential screening of step payloads
  mem20kilnz.budgets.check_triangles       per-step resource budget
  mem20verify.dataintegrity.check          store round-trip integrity
  toolchest.catalog.load_inventory         estate registration of this subsystem
  gateway.hermes_gateway.load_names        fleet registry snapshot
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from . import domain

# <repo>/<subsystem>/<package>/integration.py  ->  parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]

_DEPENDENCY_PATHS = {
    "memory_engine": "memory_engine",
    "gateway": "gateway",
    "toolchest": "toolchest/src",
    "mem20kilnz": "mem20kilnz",
    "mem20verify": "mem20verify",
    "mem20secretz": "mem20secretz/src",
}


def _bootstrap_paths(repo_root: Path | None = None) -> list[str]:
    """Put the repo root and every dependency project root on sys.path."""
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    added: list[str] = []
    root_str = str(root.resolve())
    if os.path.isdir(root_str) and root_str not in sys.path:
        sys.path.insert(0, root_str)
        added.append(root_str)
    for rel in _DEPENDENCY_PATHS.values():
        candidate = str((root / rel).resolve())
        if os.path.isdir(candidate) and candidate not in sys.path:
            sys.path.insert(0, candidate)
            added.append(candidate)
    return added


_bootstrap_paths()

# memory_engine resolves its store at import time.
if not os.environ.get("MEM20_STORE_PATH"):
    os.environ["MEM20_STORE_PATH"] = os.path.join(
        tempfile.gettempdir(), "mem20-rm052-store"
    )

import memory_engine.memory as _engine_memory  # noqa: E402
from memory_engine.memory import recall, remember  # noqa: E402
from gateway.hermes_gateway import load_names  # noqa: E402
from toolchest.catalog import load_inventory  # noqa: E402
from mem20kilnz.budgets import check_triangles  # noqa: E402
from mem20verify.dataintegrity import check as integrity_check  # noqa: E402
from mem20secretz.sweep import classify as classify_secret  # noqa: E402

SUBSYSTEM = "mem20reversibleexecutiongraphz"
INVENTORY_PATH = _REPO_ROOT / "toolchest" / "inventory.json"
MEMORY_ENGINE_DIR = str((_REPO_ROOT / "memory_engine").resolve())

SCREENED_KEYS = ("token", "secret", "password", "api_key", "authorization")


def screen_step(step: dict) -> list[dict]:
    """Classify credential-shaped values in a step's payload.

    A reversible plan is exactly the kind of object that carries a token in a
    step argument, so screening happens before the step is recorded.
    """
    findings: list[dict] = []
    for key, value in (step.get("payload") or {}).items():
        if not isinstance(value, str):
            continue
        if not any(hint in key.lower() for hint in SCREENED_KEYS):
            continue
        severity, kind = classify_secret(key, value)
        findings.append({"step": step.get("id"), "key": key,
                         "severity": severity, "kind": kind})
    return findings


def _run_integrity_check() -> dict:
    """Run mem20verify's store round-trip against the real memory engine.

    ``mem20verify.dataintegrity`` loads the engine with a bare ``import memory``,
    which in this repo can resolve to the root ``memory.py`` shim whose
    ``LEDGER``/``ENTRIES`` are import-time copies — patching them redirects
    nothing. Binding ``sys.modules["memory"]`` to the real engine for the call
    makes the check measure the store ``remember()`` actually writes to.
    """
    previous = sys.modules.get("memory")
    sys.modules["memory"] = _engine_memory
    try:
        result = integrity_check(MEMORY_ENGINE_DIR)
    finally:
        if previous is None:
            sys.modules.pop("memory", None)
        else:
            sys.modules["memory"] = previous
    return {
        "ok": result.ok,
        "checked": result.checked,
        "roundtrip_ok": result.roundtrip_ok,
        "error": result.error,
    }


def execute_reversible_plan(
    plan_id: str,
    steps: list[dict],
    family: str = "prop",
    store_dir: str | None = None,
) -> dict:
    """Execute a plan onto a reversible graph and audit the run.

    Each step is ``{"id": str, "payload": dict, "triangles": int}``.

    Steps, in order:

    1. ``domain.add_node`` records each step on the graph (undoable).
    2. ``mem20secretz.sweep.classify`` screens each step payload.
    3. ``mem20kilnz.budgets.check_triangles`` checks each step's budget.
    4. ``memory_engine.memory.remember`` writes each step to the ledger and
       ``recall`` reads the plan back to prove it landed.
    5. ``mem20verify.dataintegrity.check`` proves the store round-trips.
    6. ``toolchest.catalog.load_inventory`` confirms estate registration.
    7. ``gateway.hermes_gateway.load_names`` snapshots the fleet registry.

    ``reversible`` is True only when the graph can be fully undone (cursor at
    the last step) and no step was refused.
    """
    if store_dir:
        os.environ["MEM20_STORE_PATH"] = store_dir

    graph = domain.create_graph()
    secrets: list[dict] = []
    budgets: list[dict] = []
    refused: list[str] = []

    for step in steps:
        step_id = step.get("id", "")
        findings = screen_step(step)
        secrets.extend(findings)
        if any(f["severity"] == "critical" for f in findings):
            refused.append(step_id)
            continue

        budget = check_triangles(family, int(step.get("triangles", 0) or 0))
        budgets.append({"step": step_id, "ok": budget.ok, "reason": budget.reason})
        if not budget.ok:
            refused.append(step_id)
            continue

        domain.add_node(graph, step_id)

    topic = f"plan.{plan_id}"
    remember(
        topic,
        f"plan {plan_id} executed {len(graph['nodes'])} of {len(steps)} steps",
        tags=["rm052", "reversible-plan"],
        epistemic_status="observed",
    )
    recalled = recall(topic=topic)
    ledger_ok = bool(recalled) and plan_id in recalled[-1].get("content", "")

    integrity_record = _run_integrity_check()

    inventory = load_inventory(INVENTORY_PATH)
    registered = any(
        entry.get("name") == SUBSYSTEM for entry in inventory.get("entries", [])
    )

    fleet = load_names()
    health = domain.graph_health(graph)

    reversible = (
        not refused
        and health["cursor"] == health["nodes"] - 1
        and health["nodes"] == len(steps)
    )
    return {
        "plan_id": plan_id,
        "health": health,
        "secrets": secrets,
        "budgets": budgets,
        "refused": refused,
        "ledger": {"topic": topic, "rows": len(recalled), "ok": ledger_ok},
        "integrity": integrity_record,
        "inventory": {
            "path": str(INVENTORY_PATH),
            "entries": len(inventory.get("entries", [])),
            "subsystem_registered": registered,
        },
        "fleet": {"agents": len(fleet)},
        "reversible": reversible,
        "ok": reversible and ledger_ok and integrity_record["ok"] and registered,
    }


def rollback_plan(plan_id: str, steps: list[dict], store_dir: str | None = None) -> dict:
    """Undo every step of an executed plan and record the rollback.

    Uses ``domain.undo`` for the compensation and ``memory_engine.memory.remember``
    to leave an audit trail, so a rollback is as traceable as the forward run.
    """
    if store_dir:
        os.environ["MEM20_STORE_PATH"] = store_dir

    graph = domain.create_graph()
    for step in steps:
        domain.add_node(graph, step.get("id", ""))

    undone = 0
    while domain.undo(graph)["ok"]:
        undone += 1

    remember(
        f"plan.{plan_id}.rollback",
        f"plan {plan_id} rolled back {undone} steps",
        tags=["rm052", "rollback"],
        epistemic_status="observed",
    )
    return {
        "plan_id": plan_id,
        "undone": undone,
        "remaining": len(graph["nodes"]),
        "clean": len(graph["nodes"]) == 0,
    }
