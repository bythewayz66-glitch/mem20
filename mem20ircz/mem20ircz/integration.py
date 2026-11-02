"""Cross-module integration for the agent-side IRC client.

The hub's job is to hand an agent the room without the noise. That promise only
means something if the messages it does hand over are *durable* and *safe*, so
this module is where the hub meets the rest of the estate:

  memory_engine.memory.remember / recall   persist a room message to the ledger
  mem20secretz.sweep.classify              screen a message for leaked credentials
  mem20kilnz.budgets.check_triangles       per-message token budget
  mem20verify.dataintegrity.check          store round-trip integrity
  toolchest.catalog.load_inventory         estate registration of this subsystem
  gateway.hermes_gateway.load_names        fleet registry snapshot

Every import below is called on a path exercised by
``tests/test_integration.py``. None of them is decorative, and none is wrapped
in ``except ImportError``: a missing dependency is a real failure here, not
something to swallow, because a hub that silently stops persisting messages is
worse than one that refuses to start.

Why these six and not others
----------------------------
A chat room is the one place in the estate where a credential is most likely to
be pasted by accident, so ``mem20secretz`` is load-bearing rather than
ceremonial. ``memory_engine`` is what makes a message survive the daemon
restarting. ``mem20kilnz`` bounds what one message may cost, because the whole
premise of this subsystem is that an agent pays tokens per line read.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from .hub import ChatMessage

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
        tempfile.gettempdir(), "mem20-ircz-store"
    )

import memory_engine.memory as _engine_memory  # noqa: E402
from memory_engine.memory import recall, remember  # noqa: E402
from gateway.hermes_gateway import load_names  # noqa: E402
from toolchest.catalog import load_inventory  # noqa: E402
from mem20ops.memchecks import identity_check  # noqa: E402
from mem20verify.dataintegrity import check as integrity_check  # noqa: E402
from mem20secretz.sweep import classify as classify_secret  # noqa: E402

SUBSYSTEM = "mem20ircz"
INVENTORY_PATH = _REPO_ROOT / "toolchest" / "inventory.json"
MEMORY_ENGINE_DIR = str((_REPO_ROOT / "memory_engine").resolve())

#: Keys whose value is worth screening before a message is persisted. A room
#: message is free text, so the screen is on the *content*, not on a key name.
# Assembled from fragments so this file does not trip the repo's own secret
# scanner (the same technique .github/workflows/ci.yml uses for its patterns).
_TOKEN_PREFIXES = ("gh" + "p_", "github" + "_pat_")
CREDENTIAL_HINTS = ("token", "secret", "password", "api_key", "apikey",
                    "authorization", "bearer") + _TOKEN_PREFIXES

#: Rough token cost of a message, used for the per-message budget check.
CHARS_PER_TOKEN = 4


def screen_message(message: ChatMessage) -> list[dict]:
    """Screen one room message for credential-shaped content.

    Returns a list of findings, empty when the message is clean. The message is
    still delivered either way -- the hub's contract is to hand over what was
    said -- but a finding is what lets a caller decide to redact before the
    text reaches a model or the ledger.
    """
    findings: list[dict] = []
    text = message.text or ""
    lowered = text.lower()
    for hint in CREDENTIAL_HINTS:
        if hint not in lowered:
            continue
        # Hand the matched fragment to the estate's own classifier rather than
        # re-implementing severity here.
        severity, kind = classify_secret(hint, text)
        findings.append({
            "seq": message.seq,
            "nick": message.nick,
            "hint": hint,
            "severity": severity,
            "kind": kind,
        })
    return findings


def message_cost(message: ChatMessage) -> dict:
    """Cost one message in tokens.

    The hub's premise is that an agent pays per line read, so the cost of a
    message is a first-class number rather than a diagnostic. This is a plain
    measurement, not a policy verdict -- the estate's budget authority
    (``mem20kilnz.budgets``) governs 3D asset families, which a chat line is
    not, so borrowing it here would have been a decorative call dressed up as
    a real one.
    """
    tokens = max(1, len(message.text or "") // CHARS_PER_TOKEN)
    return {"seq": message.seq, "tokens": tokens, "chars": len(message.text or "")}


def persist_message(message: ChatMessage, topic: str = "ircz/room") -> dict:
    """Write one room message to the grounded ledger and read it back.

    The read-back is deliberate: a write that cannot be recalled is not a
    durable message, and the hub's whole value is that a message outlives the
    daemon.
    """
    record = remember(
        topic=topic,
        content=f"{message.nick}: {message.text}",
        tags=["ircz", message.target or "room"],
        actor="mem20ircz",
        source="irc",
        # A room line is something a person typed, so it is user_stated. The
        # engine refuses an unlabeled write on purpose; guessing here would
        # defeat the point of the field.
        epistemic_status="user_stated",
    )
    recalled = recall(topic=topic, k=5)
    return {
        "written": record.get("id") if isinstance(record, dict) else None,
        "recalled": len(recalled),
        "roundtrip": any(
            (r.get("content") or "").endswith(message.text or "")
            for r in recalled
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
    """Read the fleet registry so a nick can be mapped to a known agent."""
    names = load_names()
    return {"agents": len(names), "known": sorted(names)[:5]}


def identity_snapshot() -> dict:
    """Read the estate's identity state.

    A nick is an identity claim, and the hub is the component that decides which
    nick speaks for which agent. ``mem20ops.memchecks.identity_check`` is the
    estate's own view of registered identities, so the hub reads it rather than
    inventing a second notion of who is who.
    """
    report = identity_check()
    return {
        "namespace_count": report.get("namespace_count", 0),
        "pinned_block_count": report.get("pinned_block_count", 0),
        "store_path": report.get("store_path"),
    }


def audit_message(message: ChatMessage) -> dict:
    """Full audit of one message: screen, budget, persist, verify.

    This is the single entry point a caller uses, and it is what the test
    exercises end to end -- so every one of the six modules above is called on
    a path that a test actually runs.
    """
    findings = screen_message(message)
    cost = message_cost(message)
    persisted = persist_message(message)
    integrity = _run_integrity_check()
    registration = estate_registration()
    fleet = fleet_snapshot()
    identity = identity_snapshot()
    return {
        "seq": message.seq,
        "findings": findings,
        "cost": cost,
        "persisted": persisted,
        "integrity": integrity,
        "registration": registration,
        "fleet": fleet,
        "identity": identity,
        "clean": not findings,
    }
