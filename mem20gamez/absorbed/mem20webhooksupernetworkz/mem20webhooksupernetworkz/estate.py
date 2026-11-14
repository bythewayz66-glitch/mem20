"""Estate seam for the webhook supernetwork.

A webhook receiver is where untrusted structured data enters the estate, so the
sibling projects that already own the relevant judgements are consulted here
rather than re-implemented:

================  ==========================================================
mem20 project      symbol used
================  ==========================================================
``mem20secretz``   ``sweep.classify``        is this payload safe to persist
``mem20liez``      ``gates.check_prohibited_uses``  may this route exist
``mem20verify``    ``dataintegrity.check``   can the store replay faithfully
``mem20ops``       ``memchecks.identity_check``  which store is this
``memory_engine``  ``memory.validate_event_time``  is the event time legal
``toolchest``      ``catalog.load_inventory``  what does the estate expose
================  ==========================================================

Each function calls the sibling's real API and returns its real result. Around
the calls, the layout problem is the same as everywhere in the estate: the
projects have three different layouts (flat package, nested project, ``src/``),
so the roots are put on ``sys.path`` before import and a missing project is
recorded rather than crashing the import of this module.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = [
    "REPO_ROOT", "UNAVAILABLE", "estate_path", "estate_status",
    "resync_engine_store",
    "validate_event_time", "classify_payload", "check_route_legality",
    "verify_store", "identity", "tool_inventory",
]

# <repo>/mem20webhooksupernetworkz/mem20webhooksupernetworkz/estate.py
REPO_ROOT = Path(__file__).resolve().parents[2]

_FLAT = ("memory_engine", "gateway", "mem20liez", "mem20ircz", "mem20dreamz")
_NESTED = ("mem20verify",)
_SRC = ("mem20ops", "mem20secretz", "toolchest")

UNAVAILABLE: dict[str, str] = {}
_PATHS_READY = False


def _prepend(path: Path) -> None:
    text = str(path)
    if text in sys.path:
        sys.path.remove(text)
    sys.path.insert(0, text)


def estate_path() -> list[str]:
    """Put every estate project root on ``sys.path``; inner packages first.

    Idempotent, and returns the paths it added so a test can assert the wiring
    ran instead of trusting it.
    """
    global _PATHS_READY
    if _PATHS_READY:
        return []
    added: list[str] = []
    for project in reversed(_SRC):
        candidate = REPO_ROOT / project / "src"
        if candidate.is_dir():
            _prepend(candidate)
            added.append(str(candidate))
    for project in reversed(_NESTED):
        candidate = REPO_ROOT / project
        if (candidate / project / "__init__.py").is_file():
            _prepend(candidate)
            added.append(str(candidate))
    for project in reversed(_FLAT):
        candidate = REPO_ROOT / project
        if candidate.is_dir():
            _prepend(candidate)
            added.append(str(candidate))
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)
        added.append(root)
    _PATHS_READY = True
    return added


def need(symbol, name: str, project: str):
    """Return an imported estate symbol, or raise naming the project to install."""
    if symbol is None:
        raise ImportError(
            f"{name} is unavailable. It ships with the mem20 project '{project}' "
            f"at {REPO_ROOT / project}. (mem20 installs from source, not PyPI.)"
        )
    return symbol


estate_path()


def _single_engine_instance() -> bool:
    """Make ``import memory`` and ``import memory_engine.memory`` one module.

    The estate imports the SAME file under two names, and Python caches them as
    two independent modules:

        memory_engine/memory.py  ->  sys.modules["memory_engine.memory"]
                                 ->  sys.modules["memory"]   (via sys.path)

    Two module objects means two copies of ``STORE_DIR``/``LEDGER``/``ENTRIES``
    and two vector/BM25 index sets for one store. The observable failure: with
    ``MEM20_STORE_PATH`` set, one copy still points at the previous store, so
    ``mem20verify.dataintegrity`` writes rows into its copy and then reports
    "no ledger row written" - a false *integrity failure* on a perfectly good
    store, which is the worst kind of wrong answer, because it blocks replays
    and sends you looking at the data instead of the loader.

    ``mem20ops.memchecks._load_engine`` already reloads ``memory_engine.memory``
    but still does a separate ``import memory``, so the split survives that.
    Aliasing the two names is the minimal correct repair: they are one file, so
    they must be one module. Returns True when an alias was installed.
    """
    import memory_engine.memory as engine  # noqa: PLC0415 - after estate_path()

    if sys.modules.get("memory") is engine:
        return False
    # Preserve anything a loader did to the other copy before binding it: the
    # aliased object becomes the single truth, so it must carry the union of
    # both copies' path attributes rather than silently dropping one.
    previous = sys.modules.get("memory")
    if previous is not None:
        for attribute in ("STORE_DIR", "LEDGER", "ENTRIES", "SIMULATED_LEDGER"):
            mine = getattr(engine, attribute, None)
            theirs = getattr(previous, attribute, None)
            if mine is None and theirs is not None:
                setattr(engine, attribute, theirs)
    sys.modules["memory"] = engine
    return True


# Run before the symbol imports below, so every module this seam loads - and
# every module they load - sees one engine.
_single_engine_instance()


def resync_engine_store(store_path: str | None = None) -> bool:
    """Re-point the (single) engine module at ``MEM20_STORE_PATH`` and re-alias.

    The engine computes ``STORE_DIR``/``LEDGER``/``ENTRIES`` at import time. A
    long-lived process - a receiver, a supervisor, a test session - that changes
    the store afterwards keeps the old path in every module that already holds a
    reference, so writes and reads silently address different files.

    Reloading is the engine's own supported mechanism (``mem20ops.memchecks``
    does the same), and reloading also rebuilds ``sys.modules``: the plain
    ``memory`` name can end up bound to the pre-reload object, which is exactly
    the split :func:`_single_engine_instance` exists to prevent. So re-alias
    after every reload.

    Returns True when this call changed anything, so a caller can assert the
    resync ran rather than hope it did.
    """
    import importlib

    import memory_engine.memory as engine  # noqa: PLC0415 - after estate_path()

    desired = store_path or os.environ.get("MEM20_STORE_PATH")
    if not desired:
        return False
    previous = getattr(engine, "STORE_DIR", None)
    if previous != desired:
        os.environ["MEM20_STORE_PATH"] = desired
        engine = importlib.reload(engine)
    # Reload created a NEW module object; drop any stale binding and re-alias.
    if sys.modules.get("memory") is not None and sys.modules.get("memory") is not engine:
        del sys.modules["memory"]
    alias_installed = _single_engine_instance()
    return alias_installed or previous != desired

# -- static, symbol-level imports -------------------------------------------
# Symbol-level, not ``import mem20secretz``: packages in the estate re-export
# functions under submodule names (``mem20secretz/__init__.py`` does
# ``from .sweep import ... sweep ...``), so attribute-style access on the package
# resolves to a function on one checkout and a module on another.

try:
    from mem20secretz.sweep import classify as _classify_secret
except ImportError as _exc:  # pragma: no cover - only on a broken checkout
    _classify_secret = None
    UNAVAILABLE["mem20secretz.sweep"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20liez.gates import check_prohibited_uses as _check_prohibited_uses
except ImportError as _exc:  # pragma: no cover
    _check_prohibited_uses = None
    UNAVAILABLE["mem20liez.gates"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20verify.dataintegrity import check as _integrity_check
except ImportError as _exc:  # pragma: no cover
    _integrity_check = None
    UNAVAILABLE["mem20verify.dataintegrity"] = f"{type(_exc).__name__}: {_exc}"

try:
    from mem20ops.memchecks import identity_check as _identity_check
except ImportError as _exc:  # pragma: no cover
    _identity_check = None
    UNAVAILABLE["mem20ops.memchecks"] = f"{type(_exc).__name__}: {_exc}"

try:
    from memory_engine.memory import validate_event_time as _validate_event_time
except ImportError as _exc:  # pragma: no cover
    _validate_event_time = None
    UNAVAILABLE["memory_engine.memory"] = f"{type(_exc).__name__}: {_exc}"

try:
    from toolchest.catalog import load_inventory as _load_inventory
except ImportError as _exc:  # pragma: no cover
    _load_inventory = None
    UNAVAILABLE["toolchest.catalog"] = f"{type(_exc).__name__}: {_exc}"


# -- 1. memory_engine: is the webhook's event time legal? -------------------

def validate_event_time(timestamp, now: float | None = None) -> str:
    """Normalise a webhook's event time through the ledger's own validator.

    A webhook carries an event time supplied by the sender. It becomes the
    ``valid_from`` of whatever belief this event asserts, so it has to satisfy
    the same bounds as any other event time in the estate - otherwise the
    temporal layer inherits a timestamp that no other subsystem would accept.

    The sender's clock is the sender's; a wildly future time is refused by the
    ledger's own rules rather than accepted because it parses.
    """
    from datetime import datetime, timezone

    validate = need(_validate_event_time, "validate_event_time", "memory_engine")
    if isinstance(timestamp, (int, float)):
        stamp = datetime.fromtimestamp(float(timestamp), timezone.utc).isoformat()
    else:
        stamp = str(timestamp)
    # ``now`` is passed as the upper bound when supplied, so the ledger judges
    # skew against the receiving host's clock rather than its own wall clock.
    if now is not None:
        reference = datetime.fromtimestamp(float(now), timezone.utc).isoformat()
        return validate(stamp, now=reference)
    return validate(stamp)


# -- 2. mem20secretz: is this payload safe to persist, log or replay? -------

def classify_payload(payload, header_names=()) -> dict:
    """Classify what a webhook carries before it reaches the event log.

    Two halves, because either alone misses real cases:

    * **by key** - a payload with a field named ``token``/``secret``/``api_key``
      is a credential whatever it holds. Signature headers are in the same
      class: ``X-Hub-Signature-256`` is keyed, not a bearer credential, but a
      payload that carries the shared secret itself is not safe to persist.
    * **by value** - a high-entropy opaque string under a neutral key is very
      often a token. Classifying only keys would let it through.

    The more severe answer wins. The caller decides what to do (this returns a
    verdict, never mutates the payload): :class:`WebhookSuperNetwork` refuses to
    admit an unsafe payload to its event log, because that log is a durable
    replayable record.
    """
    classify = need(_classify_secret, "sweep.classify", "mem20secretz")
    order = {"critical": 0, "high": 1, "info": 2}

    worst = ("info", "none", None)
    for name, value in _flatten(payload):
        for probe_name, probe_value in ((name, value), (name, "")):
            severity, kind = classify(str(probe_name), str(probe_value))
            if order.get(severity, 9) < order.get(worst[0], 9):
                worst = (severity, kind, probe_name)

    header_state = "no-headers"
    for header in header_names:
        severity, kind = classify(str(header), "")
        if order.get(severity, 9) < order.get(worst[0], 9):
            worst = (severity, kind, str(header))
            header_state = "header-named-credential"

    severity, kind, field = worst
    return {
        "safe": severity != "critical",
        "severity": severity,
        "kind": kind,
        "field": field,
        "header_state": header_state,
        "classifier": "mem20secretz.sweep.classify",
        "policy": "a critical (credential-named) payload is refused entry to "
                  "the durable event log; it can be verified and routed, but "
                  "not stored verbatim",
    }


def _flatten(payload, prefix: str = "") -> list[tuple[str, object]]:
    """``(dotted-name, value)`` pairs for every leaf in a nested payload."""
    out: list[tuple[str, object]] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            name = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, (dict, list)):
                out.extend(_flatten(value, name))
            else:
                out.append((name, value))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            name = f"{prefix}[{index}]"
            if isinstance(value, (dict, list)):
                out.extend(_flatten(value, name))
            else:
                out.append((name, value))
    elif prefix:
        out.append((prefix, payload))
    return out


# -- 3. mem20liez: may this route exist at all? ----------------------------

def check_route_legality(intended_uses=None) -> dict:
    """Refuse a route whose declared use is on the estate's prohibited list.

    A webhook network is a general fan-out: whatever a route is declared for,
    the network will deliver it, retry it and keep a replayable copy. So the
    refusal list has to be consulted where the route is registered, not left to
    whoever wires the consumer.

    Raises ``mem20liez.gates.GateError``; returns the permitted verdict.
    """
    gate = need(_check_prohibited_uses, "gates.check_prohibited_uses", "mem20liez")
    uses = list(intended_uses) if intended_uses is not None else ["webhook_routing"]
    gate(uses)
    return {"permitted": True, "uses": uses,
            "gate": "mem20liez.gates.check_prohibited_uses"}


# -- 4. mem20verify: can this store replay faithfully? ---------------------

def verify_store(engine_dir: str | None = None) -> dict:
    """Prove the store a replay reads from can round-trip a write.

    ``replay()`` re-executes events from the log. If the store underneath is
    damaged, the replay re-delivers a *subset* - silently, and looking like a
    legitimate partial replay. ``mem20verify.dataintegrity.check`` is the only
    evidence available here that the log is trustworthy before it is replayed.
    """
    checker = need(_integrity_check, "dataintegrity.check", "mem20verify")
    return checker(engine_dir or str(REPO_ROOT / "memory_engine")).as_dict()


# -- 5. mem20ops: which store is this receiver writing into? ---------------

def identity(store_path: str | None = None) -> dict:
    """Identify the store this receiver is about to record deliveries into.

    A webhook network accepts unsigned shapes from anyone who knows the URL.
    Recording them into an unidentified store is how one host's deliveries end
    up attributed to another's log.
    """
    return need(_identity_check, "identity_check", "mem20ops")(store_path)


# -- 6. toolchest: what does the estate expose for routing? ---------------

def tool_inventory(limit: int = 5) -> dict:
    """The estate's tool inventory, from the catalog's own reader.

    A route is declared against a capability. Consulting the catalog means the
    network routes to something the estate actually exposes, and the count in
    the metrics snapshot is measured rather than asserted.
    """
    load = need(_load_inventory, "catalog.load_inventory", "toolchest")
    path = REPO_ROOT / "toolchest" / "inventory.json"
    if not path.is_file():
        return {"source": "toolchest.catalog.load_inventory", "total": 0,
                "sample": [], "error": f"no inventory at {path}"}
    inventory = load(path)
    entries = inventory.get("entries") if isinstance(inventory, dict) else None
    if isinstance(entries, list):
        names = [str(e.get("name", e)) if isinstance(e, dict) else str(e)
                 for e in entries]
    elif isinstance(inventory, dict):
        names = sorted(inventory.keys())
    else:  # pragma: no cover - catalog contract changed
        names = []
    return {
        "source": "toolchest.catalog.load_inventory",
        "total": len(names),
        "sample": names[:limit],
    }


def estate_status() -> dict:
    """One call answering 'is this receiver's estate reachable?', per project."""
    symbols = {
        "mem20secretz": _classify_secret,
        "mem20liez": _check_prohibited_uses,
        "mem20verify": _integrity_check,
        "mem20ops": _identity_check,
        "memory_engine": _validate_event_time,
        "toolchest": _load_inventory,
    }
    return {
        "repo_root": str(REPO_ROOT),
        "wired": sorted(name for name, sym in symbols.items() if sym is not None),
        "unavailable": dict(UNAVAILABLE),
    }
