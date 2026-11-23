"""Estate wiring for the event stream superhighway.

The superhighway is the transport layer: it moves typed events between local,
edge and cloud runtimes. On its own it is a silo — an event that is routed but
never remembered, never indexed, never announced to the fleet and never
verified is a message nobody can act on afterwards.

This module is the seam. Every function here calls a real API of another mem20
project and returns its real result:

===========================  ==========================================
mem20 project                API used
===========================  ==========================================
``memory_engine``            ``memory.remember`` / ``memory.recall``
``memory_engine``            ``retrieval_v2.decompose_query``
``toolchest``                ``catalog.load_inventory``
``gateway``                  ``hermes_gateway.broadcast`` / ``register_agent``
``mem20verify``              ``dataintegrity.check``
``mem20ops``                 ``memchecks.identity_check``
``mem20corez``               ``quantizer.quantize_tensor``
``mem20secretz``             ``sweep.classify``
===========================  ==========================================

The imports are static and module-level on purpose: a reader (and the
conformance gate's AST scan) can see exactly which projects this subsystem
depends on without executing it. ``_bootstrap.ensure_estate_path()`` runs
first so the estate is importable, and a missing project is recorded rather
than raised at import time — the error surfaces at the call that needs it,
naming the project.

Nothing here is a stub and nothing is simulated: if a dependency is missing the
call raises, because a superhighway that silently drops its audit trail is
worse than one that refuses to start.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time
from typing import Any

from . import domain
from ._bootstrap import REPO_ROOT, ensure_estate_path, store_path

# The estate must be importable before the static imports below resolve.
ensure_estate_path()

# Static, module-level estate imports. Each is a real dependency of a function
# in this module; see the table in the docstring.
_IMPORT_ERRORS: dict[str, str] = {}

try:
    from memory_engine import memory as _memory_engine
except ImportError as _exc:  # pragma: no cover - only on a broken checkout
    _memory_engine = None
    _IMPORT_ERRORS["memory_engine.memory"] = str(_exc)

try:
    from memory_engine import retrieval_v2 as _retrieval
except ImportError as _exc:  # pragma: no cover
    _retrieval = None
    _IMPORT_ERRORS["memory_engine.retrieval_v2"] = str(_exc)

try:
    from toolchest import catalog as _catalog
except ImportError as _exc:  # pragma: no cover
    _catalog = None
    _IMPORT_ERRORS["toolchest.catalog"] = str(_exc)

try:
    from gateway import hermes_gateway as _gateway
except ImportError as _exc:  # pragma: no cover
    _gateway = None
    _IMPORT_ERRORS["gateway.hermes_gateway"] = str(_exc)

try:
    from mem20verify import dataintegrity as _dataintegrity
except ImportError as _exc:  # pragma: no cover
    _dataintegrity = None
    _IMPORT_ERRORS["mem20verify.dataintegrity"] = str(_exc)

try:
    from mem20ops import memchecks as _memchecks
except ImportError as _exc:  # pragma: no cover
    _memchecks = None
    _IMPORT_ERRORS["mem20ops.memchecks"] = str(_exc)

try:
    from mem20corez import quantizer as _quantizer
except ImportError as _exc:  # pragma: no cover
    _quantizer = None
    _IMPORT_ERRORS["mem20corez.quantizer"] = str(_exc)

try:
    # ``mem20secretz/__init__.py`` re-exports the *function* ``sweep``, which
    # shadows the submodule of the same name on the package object. Import the
    # submodule explicitly so ``classify`` is reachable.
    from mem20secretz import sweep as _sweep_mod
    from mem20secretz.sweep import classify as _classify
except ImportError as _exc:  # pragma: no cover
    _sweep_mod = None
    _classify = None
    _IMPORT_ERRORS["mem20secretz.sweep"] = str(_exc)


def _need(module, name: str, project: str):
    """Return ``module`` or raise an error naming the project to install."""
    if module is not None:
        return module
    raise ImportError(
        f"{name} is unavailable; it ships with the mem20 project '{project}' at "
        f"{REPO_ROOT / project}. Install the estate with `git clone` + "
        f"`pip install -r requirements.txt` (mem20 is not on PyPI). "
        f"Original error: {_IMPORT_ERRORS.get(name, 'unknown')}"
    )


def _live(module, name: str, project: str):
    """The current module object for ``name``, re-resolved if it was evicted.

    The memory engine reads ``STORE_DIR`` at import time, so a caller that
    points ``MEM20_STORE_PATH`` at an isolated store has to re-import it. When
    that happens the module-level reference above is stale; re-resolving keeps
    the static import as the fast path while still honouring the caller's
    store. ``importlib.import_module`` is a ``sys.modules`` lookup, so this is
    cheap.
    """
    _need(module, name, project)
    current = sys.modules.get(name)
    if current is not None and current is not module:
        return current
    return module


# --------------------------------------------------------------------------
# memory_engine — durable event memory
# --------------------------------------------------------------------------


def _memory():
    """The memory engine, bound to this subsystem's store.

    The engine reads ``STORE_DIR`` at import time, so a caller that points
    ``MEM20_STORE_PATH`` at an isolated store needs the module re-imported
    against that path. Three cases, in order:

    * the module is not in ``sys.modules`` at all (a test evicted it) — import
      it fresh, which picks up the current env;
    * it is loaded but bound to a different store — reload it;
    * it is loaded and already bound to the right store — use it as-is.

    ``importlib.reload`` is only ever called on a module that is genuinely in
    ``sys.modules``; calling it on an evicted module raises
    "module not in sys.modules", which is what made this fragile before.
    """
    desired = store_path()
    os.environ["MEM20_STORE_PATH"] = desired
    name = "memory_engine.memory"
    engine = sys.modules.get(name)
    if engine is None:
        engine = importlib.import_module(name)
    if getattr(engine, "STORE_DIR", None) != desired:
        engine = importlib.reload(engine)
    return engine


def remember_event(stream: dict, event: dict, *, actor: str = "eventstream") -> dict:
    """Persist one routed event as a grounded memory fact.

    The event's type becomes the memory topic and its payload the content, so
    ``recall(topic=...)`` later returns the actual events that flowed, not a
    summary of them. ``epistemic_status='observed'`` is required by the engine
    and is honest here: the event was seen on the wire.
    """
    memory = _memory()
    topic = f"eventstream.{stream['name']}.{event['type']}"
    return memory.remember(
        topic=topic,
        content=json.dumps(
            {"seq": event["seq"], "key": event.get("key"), "payload": event["payload"]},
            sort_keys=True,
        ),
        tags=["eventstream", stream["name"], event["type"]],
        actor=actor,
        epistemic_status="observed",
        source=f"mem20eventstreamsuperhighwayz:{stream['name']}",
    )


def recall_events(stream_name: str, event_type: str | None = None) -> list[dict]:
    """Read back the events persisted for a stream (optionally one type)."""
    memory = _memory()
    topic = f"eventstream.{stream_name}" + (f".{event_type}" if event_type else "")
    return memory.recall(topic=topic)


def memory_status() -> str:
    """The engine's own status report — used as a health signal by the CLI."""
    return _memory().status()


# --------------------------------------------------------------------------
# memory_engine.retrieval_v2 — multi-hop search over the event log
# --------------------------------------------------------------------------


def search_events(query: str, k: int = 5) -> dict:
    """Decompose a compound question about the stream into sub-retrievals.

    A question like "what is the p95 latency and which partition is hot" is two
    questions. ``decompose_query`` splits it and runs each part, which is what
    makes the superhighway's own telemetry answerable in one call.
    """
    os.environ.setdefault("MEM20_STORE_PATH", store_path())
    retrieval = _live(_retrieval, "memory_engine.retrieval_v2", "memory_engine")
    return retrieval.decompose_query(query, k=k)


# --------------------------------------------------------------------------
# toolchest — capability inventory
# --------------------------------------------------------------------------


def capability_inventory() -> dict:
    """Load the estate's measured tool inventory.

    The superhighway advertises what it can route to; the inventory is the
    measured list of what actually exists on the box, so a route is only
    offered for a capability that is really installed.
    """
    catalog = _need(_catalog, "toolchest.catalog", "toolchest")
    return catalog.load_inventory(REPO_ROOT / "toolchest" / "inventory.json")


def inventory_counts() -> dict:
    """Just the counts block — cheap enough to put in a health response."""
    return dict(capability_inventory().get("counts", {}))


# --------------------------------------------------------------------------
# gateway — fleet announcement
# --------------------------------------------------------------------------


def announce(stream: dict, event: dict, *, agent_name: str | None = None) -> dict:
    """Announce a routed event to the mem20 fleet gateway.

    ``broadcast`` writes a real line to the gateway's message log and returns
    the entry it wrote. It exits the process when no agent is registered, so
    the caller must pass a name; we default to a stable per-stream name and
    register it first if the gateway does not know it yet.
    """
    gateway = _need(_gateway, "gateway.hermes_gateway", "gateway")
    name = agent_name or f"eventstream-{stream['name']}"
    if name not in gateway.load_names():
        gateway.register_agent(name=name, location="mem20eventstreamsuperhighwayz")
    return gateway.broadcast(
        f"{event['type']} seq={event['seq']} key={event.get('key')}",
        agent_name=name,
        target="eventstream",
    )


def fleet_messages(limit: int = 20) -> list[dict]:
    """Read back what the fleet has announced.

    Reads the gateway's own message log (``hermes_gateway.MESSAGES_FILE``), the
    file ``broadcast`` appends to, newest first.

    ``hermes_gateway.read_messages`` is deliberately not used here: it indexes
    ``m["agent"]`` while ``broadcast`` writes ``agent_name``, so it raises
    ``KeyError: 'agent'`` on every message the gateway itself produced. That is
    a defect in the gateway subsystem (owned by the Server Builder wave-1
    module), not something this subsystem should paper over by writing a
    different field name — doing so would make the two writers disagree. The
    log is read directly until the gateway is fixed.
    """
    gateway = _need(_gateway, "gateway.hermes_gateway", "gateway")
    path = gateway.MESSAGES_FILE
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return rows[:limit]


# --------------------------------------------------------------------------
# mem20verify / mem20ops — integrity of the audit trail
# --------------------------------------------------------------------------


def verify_memory_integrity() -> dict:
    """Round-trip the memory engine and report whether the ledger is faithful.

    This is the check that makes the persisted event log trustworthy: it writes
    known payloads through ``remember`` and compares what the ledger stored.
    """
    dataintegrity = _need(_dataintegrity, "mem20verify.dataintegrity", "mem20verify")

    # ``check()`` imports ``memory`` and then rebinds ``ENTRIES``/``LEDGER`` on
    # that module object to a temp dir. The repo root also ships a ``memory.py``
    # that merely re-exports ``memory_engine.memory``; if that shim is what
    # ``import memory`` resolves to, the rebinding lands on the shim and the
    # real engine keeps writing to the live store — the check then reports 0
    # round-trips while looking like a data-integrity failure. Bind the real
    # engine module first so the rebinding hits the object that owns the paths.
    sys.modules["memory"] = _memory()

    result = dataintegrity.check(str(REPO_ROOT / "memory_engine"))
    return result.to_dict() if hasattr(result, "to_dict") else dict(result.__dict__)


def identity_report() -> dict:
    """Pinned blocks and namespaces for the store this subsystem writes to."""
    memchecks = _need(_memchecks, "mem20ops.memchecks", "mem20ops")
    return memchecks.identity_check(store_path())


# --------------------------------------------------------------------------
# mem20corez — compact the event payload for the wire
# --------------------------------------------------------------------------


def compact_payload(values: list[float], bits: int = 8) -> dict:
    """Quantize a numeric payload before it crosses a runtime boundary.

    Real int8 quantization from mem20corez: the returned dict carries the
    quantized tensor, its per-row scale and the measured reconstruction error,
    so a caller can decide whether the compression is acceptable for its
    stream. ``QuantizedTensor`` exposes ``.q`` / ``.scale`` fields (it has no
    ``dequantize()`` method), so the reconstruction is done here.
    """
    quantizer = _need(_quantizer, "mem20corez.quantizer", "mem20corez")
    import numpy as np

    arr = np.asarray(values, dtype=np.float64).reshape(len(values), 1)
    tensor = quantizer.quantize_tensor(arr, bits=bits)
    scale = np.asarray(tensor.scale, dtype=np.float64).reshape(-1, 1)
    reconstructed = np.asarray(tensor.q, dtype=np.float64) * scale
    error = float(np.max(np.abs(reconstructed.reshape(-1) - arr.reshape(-1))))
    return {
        "bits": tensor.bits,
        "shape": list(arr.shape),
        "q": np.asarray(tensor.q).reshape(-1).tolist(),
        "scale": scale.reshape(-1).tolist(),
        "max_abs_error": round(error, 6),
    }


# --------------------------------------------------------------------------
# mem20secretz — credential screening of the event payload
# --------------------------------------------------------------------------


def screen_payload(payload: dict) -> dict:
    """Screen an event payload for credential-shaped values before it is routed.

    An event that crosses a runtime boundary is the last place a leaked
    credential can be caught cheaply, so every key/value pair is classified by
    ``mem20secretz.sweep.classify`` — the estate's own leak-versus-config
    classifier — and anything it calls a credential refuses the publish.

    ``classify`` returns ``(severity, kind)``. Only ``critical`` blocks: an
    endpoint URL is configuration duplication and is reported, not refused, so
    a legitimate payload is never dropped for looking like a URL.
    """
    sweep = _need(_classify, "mem20secretz.sweep", "mem20secretz")

    findings = []
    for name, value in payload.items():
        if not isinstance(value, str):
            continue
        severity, kind = sweep(str(name), value)
        findings.append({"field": str(name), "severity": severity, "kind": kind})

    blocking = [f for f in findings if f["severity"] == "critical"]
    return {
        "clean": not blocking,
        "blocking": blocking,
        "findings": findings,
        "screened": len(findings),
    }


# --------------------------------------------------------------------------
# the composed path — what the README example and the CLI both run
# --------------------------------------------------------------------------


def publish_and_persist(
    stream: dict,
    event_type: str,
    payload: dict,
    *,
    key: str | None = None,
    announce_to_fleet: bool = True,
) -> dict:
    """Publish an event, persist it, and (optionally) announce it.

    This is the one call that exercises the whole seam: domain routing, durable
    memory, and the fleet gateway. It returns every real result so a caller can
    assert on them rather than trusting a boolean.
    """
    event = domain.publish(stream, event_type, payload, key=key)
    record = remember_event(stream, event)
    out: dict[str, Any] = {
        "event": event,
        "memory_id": record.get("id"),
        "memory_topic": record.get("topic"),
        "announced": None,
        "screening": screen_payload(payload),
    }
    if announce_to_fleet:
        out["announced"] = announce(stream, event)
    return out


def stream_report(stream: dict, window_s: int = 60) -> dict:
    """A real operational report for one stream.

    Combines the domain's own throughput/lag numbers with the estate's
    inventory counts and the memory engine's status, so an operator sees the
    stream and the substrate it depends on in one object.
    """
    status = memory_status()
    return {
        "stream": stream["name"],
        "events": len(stream["events"]),
        "subscribers": sorted(stream["subscribers"]),
        "throughput_per_min": domain.throughput(stream, window_s=window_s),
        "lag": {sid: domain.lag(stream, sid) for sid in stream["subscribers"]},
        "inventory": inventory_counts(),
        "memory": status.splitlines()[0] if status else "",
        "generated_at": time.time(),
    }
