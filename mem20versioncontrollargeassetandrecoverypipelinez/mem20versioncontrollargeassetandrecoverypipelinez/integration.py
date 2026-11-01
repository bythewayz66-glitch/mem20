"""Cross-module integration for the version-control / large-asset / recovery pipeline.

This module is the seam between RM-239 and the rest of the mem20 estate. It is
deliberately *not* a thin re-export: every function below is called on a real
code path that a test exercises, and each one contributes a distinct fact to the
release audit record.

Modules used (six, all real mem20 code):

  memory_engine.memory.remember / recall   grounded ledger write + read-back
  mem20secretz.sweep.classify              credential-shaped metadata screening
  mem20kilnz.budgets.check_triangles       asset budget conformance
  mem20verify.dataintegrity.check          store round-trip integrity
  toolchest.catalog.load_inventory         estate registration of this subsystem
  gateway.hermes_gateway.load_names        fleet registry snapshot

The estate keeps each subsystem in its own project directory, so the import
paths are bootstrapped the same way the repository conftest does it: the project
root (not the repo root) goes on sys.path for each dependency.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from . import domain

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
# <repo>/<subsystem>/<package>/integration.py  ->  parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]

# project directory -> the directory that must be on sys.path for its import
_DEPENDENCY_PATHS = {
    "memory_engine": "memory_engine",
    "gateway": "gateway",
    "toolchest": "toolchest/src",
    "mem20kilnz": "mem20kilnz",
    "mem20verify": "mem20verify",
    "mem20secretz": "mem20secretz/src",
}


def _bootstrap_paths(repo_root: Path | None = None) -> list[str]:
    """Put every dependency project root on sys.path. Returns the paths added."""
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    added: list[str] = []
    # The repo root itself must be importable so `memory_engine` and `gateway`
    # resolve as packages when this module is imported from outside the repo.
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

# memory_engine resolves its store at import time, so the store location has to
# be decided before the import below. A caller that wants a specific store sets
# MEM20_STORE_PATH itself; otherwise we use a private temp store so an audit
# never writes into the operator's live ledger.
if not os.environ.get("MEM20_STORE_PATH"):
    os.environ["MEM20_STORE_PATH"] = os.path.join(
        tempfile.gettempdir(), "mem20-rm239-store"
    )

import memory_engine.memory as _engine_memory  # noqa: E402
from memory_engine.memory import recall, remember  # noqa: E402
from gateway.hermes_gateway import load_names  # noqa: E402
from toolchest.catalog import load_inventory  # noqa: E402
from mem20kilnz.budgets import check_triangles  # noqa: E402
from mem20verify.dataintegrity import check as integrity_check  # noqa: E402
from mem20secretz.sweep import classify as classify_secret  # noqa: E402

SUBSYSTEM = "mem20versioncontrollargeassetandrecoverypipelinez"
INVENTORY_PATH = _REPO_ROOT / "toolchest" / "inventory.json"
MEMORY_ENGINE_DIR = str((_REPO_ROOT / "memory_engine").resolve())

# Metadata keys whose values are screened for credential shapes before an asset
# version is recorded. A large-asset pipeline routinely carries tokens in its
# manifest, so this is the natural place to catch one.
SCREENED_KEYS = ("token", "secret", "password", "api_key", "authorization")


def screen_metadata(metadata: dict | None) -> list[dict]:
    """Classify every credential-shaped value in an asset manifest.

    Returns one record per screened key. ``severity`` comes from
    mem20secretz.sweep.classify, so the pipeline inherits the estate's single
    definition of what counts as a credential rather than inventing its own.
    """
    findings: list[dict] = []
    for key, value in (metadata or {}).items():
        if not isinstance(value, str):
            continue
        if not any(hint in key.lower() for hint in SCREENED_KEYS):
            continue
        severity, kind = classify_secret(key, value)
        findings.append({"key": key, "severity": severity, "kind": kind})
    return findings


def _run_integrity_check() -> dict:
    """Run mem20verify's store round-trip against the real memory engine.

    ``mem20verify.dataintegrity`` loads the engine with a bare ``import memory``.
    In this estate the repo root also ships a ``memory.py`` shim that re-exports
    the engine's API, so that bare import can resolve to the shim. The shim's
    ``LEDGER``/``ENTRIES`` are copies taken at import time, so patching them (as
    the integrity check does) redirects nothing and every payload reports "no
    ledger row written".

    Binding ``sys.modules["memory"]`` to the real engine module for the duration
    of the call makes the check measure the engine that ``remember()`` actually
    writes to. The previous binding is restored afterwards.
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


def audit_asset_release(
    asset_id: str,
    content: str,
    family: str = "prop",
    triangles: int = 0,
    metadata: dict | None = None,
    store_dir: str | None = None,
) -> dict:
    """Record one asset version and audit it against the rest of the estate.

    Steps, in order:

    1. ``domain.version_asset`` hashes the content into a version record.
    2. ``mem20secretz.sweep.classify`` screens the manifest for credentials.
    3. ``mem20kilnz.budgets.check_triangles`` checks the asset budget.
    4. ``memory_engine.memory.remember`` writes the version to the grounded
       ledger, and ``recall`` reads it back to prove it landed.
    5. ``mem20verify.dataintegrity.check`` proves the store round-trips.
    6. ``toolchest.catalog.load_inventory`` confirms this subsystem is a
       registered estate entry.
    7. ``gateway.hermes_gateway.load_names`` snapshots the fleet registry.

    ``ok`` is True only when the version was recorded, no credential was found,
    the budget passed, the ledger read-back matched, and the store round-tripped.
    """
    if store_dir:
        os.environ["MEM20_STORE_PATH"] = store_dir

    version = domain.version_asset(asset_id, content)

    secrets = screen_metadata(metadata)
    critical = [f for f in secrets if f["severity"] == "critical"]

    budget = check_triangles(family, int(triangles))
    budget_record = {
        "family": budget.family,
        "triangles": budget.triangles,
        "ok": budget.ok,
        "reason": budget.reason,
        "tier": budget.tier,
    }

    topic = f"asset.{asset_id}"
    remember(
        topic,
        f"{asset_id} version {version['version']} sha256 {version['hash']}",
        tags=["rm239", "asset-version"],
        epistemic_status="observed",
    )
    recalled = recall(topic=topic)
    ledger_ok = bool(recalled) and version["hash"] in recalled[-1].get("content", "")

    integrity_record = _run_integrity_check()

    inventory = load_inventory(INVENTORY_PATH)
    registered = any(
        entry.get("name") == SUBSYSTEM for entry in inventory.get("entries", [])
    )

    fleet = load_names()

    ok = (
        ledger_ok
        and not critical
        and budget.ok
        and integrity_record["ok"]
        and registered
    )
    return {
        "asset_id": asset_id,
        "version": version,
        "secrets": secrets,
        "budget": budget_record,
        "ledger": {"topic": topic, "rows": len(recalled), "ok": ledger_ok},
        "integrity": integrity_record,
        "inventory": {
            "path": str(INVENTORY_PATH),
            "entries": len(inventory.get("entries", [])),
            "subsystem_registered": registered,
        },
        "fleet": {"agents": len(fleet)},
        "ok": ok,
    }


def recover_asset(versions: list[dict], target_version: str) -> dict:
    """Recover a specific version and record the recovery in the ledger.

    Uses ``domain.recover`` for the lookup and ``memory_engine.memory.remember``
    to leave an audit trail of the recovery itself, which is what makes the
    pipeline's recovery step traceable rather than silent.
    """
    found = domain.recover(versions, target_version)
    if found is None:
        return {"recovered": False, "target": target_version}
    remember(
        f"asset.{found['asset_id']}.recovery",
        f"recovered version {target_version} sha256 {found['hash']}",
        tags=["rm239", "recovery"],
        epistemic_status="observed",
    )
    return {"recovered": True, "target": target_version, "version": found}
