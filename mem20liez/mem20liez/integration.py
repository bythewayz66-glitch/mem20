"""Cross-module integration for the behavioural-signal detector.

A detection result is a *claim about a person*. That makes this subsystem the
one in the estate where an unlabeled or unaudited write is least acceptable, so
this module is where a detection meets the rest of the estate:

  memory_engine.memory.remember / recall   persist a detection with its basis
  mem20secretz.sweep.classify              screen raw features for leaked PII
  mem20ops.memchecks.identity_check        who the session belongs to
  mem20verify.dataintegrity.check          store round-trip integrity
  toolchest.catalog.load_inventory         estate registration of this subsystem
  gateway.hermes_gateway.load_names        fleet registry snapshot

Every import below is called on a path exercised by
``tests/test_integration.py``. None is decorative and none is wrapped in
``except ImportError``: a detector that silently stops recording its basis is
worse than one that refuses to start.

Why the epistemic label matters here specifically
-------------------------------------------------
``memory_engine.remember`` refuses an unlabeled write. For most subsystems that
is a formality; here it is the whole point. A deception signal is an
*inference*, never an observation -- the observation is a micro-expression or a
pitch shift, and "this person is lying" is a conclusion drawn from it. Writing
it as anything other than ``inferred`` would launder a guess into a fact, which
is exactly the failure mode this product exists to prevent.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from .types import DetectionResult

# <repo>/<subsystem>/<package>/integration.py  ->  parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]

_DEPENDENCY_PATHS = {
    "memory_engine": "memory_engine",
    "gateway": "gateway",
    "toolchest": "toolchest/src",
    "mem20ops": "mem20ops/src",
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
        tempfile.gettempdir(), "mem20-liez-store"
    )

import memory_engine.memory as _engine_memory  # noqa: E402
from memory_engine.memory import recall, remember  # noqa: E402
from gateway.hermes_gateway import load_names  # noqa: E402
from toolchest.catalog import load_inventory  # noqa: E402
from mem20ops.memchecks import identity_check  # noqa: E402
from mem20verify.dataintegrity import check as integrity_check  # noqa: E402
from mem20secretz.sweep import classify as classify_secret  # noqa: E402

SUBSYSTEM = "mem20liez"
INVENTORY_PATH = _REPO_ROOT / "toolchest" / "inventory.json"
MEMORY_ENGINE_DIR = str((_REPO_ROOT / "memory_engine").resolve())

#: Raw feature keys that could carry a credential or an identifier. A detector
#: receives raw frames and audio features, so this is a real surface, not a
#: hypothetical one.
SENSITIVE_HINTS = ("token", "secret", "password", "api_key", "authorization",
                   "email", "phone", "ssn", "address")


def screen_features(result: DetectionResult) -> list[dict]:
    """Screen a detection's raw features for credential- or PII-shaped values.

    Returns findings, empty when clean. The detection is still recorded either
    way -- screening informs the caller, it does not suppress the signal.
    """
    findings: list[dict] = []
    features = result.raw_features or {}
    for key, value in features.items():
        if not isinstance(value, str):
            continue
        lowered = key.lower()
        for hint in SENSITIVE_HINTS:
            if hint not in lowered:
                continue
            severity, kind = classify_secret(key, value)
            findings.append({
                "signal": result.signal.value if hasattr(result.signal, "value")
                else str(result.signal),
                "key": key,
                "hint": hint,
                "severity": severity,
                "kind": kind,
            })
            break
    return findings


def persist_detection(result: DetectionResult, topic: str = "liez/detections") -> dict:
    """Write one detection to the grounded ledger and read it back.

    The epistemic status is ``inferred`` and not negotiable: a deception signal
    is a conclusion drawn from an observation, and recording it as anything
    stronger would turn a guess into a fact.
    """
    signal = result.signal.value if hasattr(result.signal, "value") else str(result.signal)
    record = remember(
        topic=topic,
        content=f"{signal} value={result.value!r} confidence={result.confidence.score}",
        tags=["liez", signal],
        actor="mem20liez",
        source="detector",
        epistemic_status="inferred",
        confidence=result.confidence.score,
    )
    recalled = recall(topic=topic, k=5)
    return {
        "written": record.get("id") if isinstance(record, dict) else None,
        "recalled": len(recalled),
        "roundtrip": any(
            signal in (r.get("content") or "") for r in recalled
        ),
    }


def _run_integrity_check() -> dict:
    """Run mem20verify's store round-trip against the real memory engine.

    ``mem20verify.dataintegrity`` loads the engine with a bare ``import
    memory``, which in this repo can resolve to the root ``memory.py`` shim
    whose ``LEDGER``/``ENTRIES`` are import-time copies -- patching them
    redirects nothing. Binding ``sys.modules["memory"]`` to the real engine for
    the call makes the check measure the store ``remember()`` actually writes to.
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


def estate_registration() -> dict:
    """Confirm this subsystem is listed in the estate inventory."""
    inventory = load_inventory(INVENTORY_PATH)
    entries = inventory.get("entries") or []
    names = set()
    for entry in entries:
        if isinstance(entry, dict):
            for key in ("name", "tool", "subsystem", "id"):
                if entry.get(key):
                    names.add(str(entry[key]))
    return {"registered": SUBSYSTEM in names, "inventory_size": len(names)}


def fleet_snapshot() -> dict:
    """Read the fleet registry so a session can be attributed to an agent."""
    names = load_names()
    return {"agents": len(names), "known": sorted(names)[:5]}


def identity_snapshot() -> dict:
    """Read the estate's identity state for the session's subject.

    A behavioural session is about a specific person, so the estate's own view
    of registered identities is the right source for who that is -- not a
    second notion invented here.
    """
    report = identity_check()
    return {
        "namespace_count": report.get("namespace_count", 0),
        "pinned_block_count": report.get("pinned_block_count", 0),
        "store_path": report.get("store_path"),
    }


def audit_detection(result: DetectionResult) -> dict:
    """Full audit of one detection: screen, persist, verify, attribute.

    This is the single entry point a caller uses, and it is what the test
    exercises end to end -- so every one of the six modules above is called on
    a path that a test actually runs.
    """
    findings = screen_features(result)
    persisted = persist_detection(result)
    integrity = _run_integrity_check()
    registration = estate_registration()
    fleet = fleet_snapshot()
    identity = identity_snapshot()
    return {
        "signal": result.signal.value if hasattr(result.signal, "value")
        else str(result.signal),
        "findings": findings,
        "persisted": persisted,
        "integrity": integrity,
        "registration": registration,
        "fleet": fleet,
        "identity": identity,
        "clean": not findings,
    }
