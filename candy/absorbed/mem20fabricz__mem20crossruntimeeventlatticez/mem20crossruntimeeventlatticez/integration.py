"""Estate wiring for the cross-runtime event lattice.

The lattice is the causality layer: it emits typed events, orders them, links
them into a vector-clock DAG and merges independent lattices into one. What it
could not do before 4.0 is *prove* anything about that history — an event that
is ordered but not durable, not searchable, not announced and not verified is a
claim, not a record.

This module is the seam. Every function calls a real API of another mem20
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
===========================  ==========================================

Imports are static and module-level so a reader — and the conformance gate's
AST scan — can see the dependency set without executing the module. A missing
project is recorded rather than raised at import time; the error surfaces at
the call that needs it, naming the project.
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
    """The current module object for ``name``, re-resolved if it was evicted."""
    _need(module, name, project)
    current = sys.modules.get(name)
    if current is not None and current is not module:
        return current
    return module


# --------------------------------------------------------------------------
# memory_engine — durable lattice history
# --------------------------------------------------------------------------


def _memory():
    """The memory engine, bound to this subsystem's store.

    The engine reads ``STORE_DIR`` at import time, so a caller pointing
    ``MEM20_STORE_PATH`` at an isolated store needs the module re-imported
    against that path. ``importlib.reload`` is only called on a module that is
    genuinely in ``sys.modules`` — calling it on an evicted module raises
    "module not in sys.modules".
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


def remember_event(event: dict, *, lattice: str = "default", actor: str = "lattice") -> dict:
    """Persist one lattice event as a grounded memory fact.

    The topic encodes lattice and event type, so a later ``recall`` returns the
    events that actually happened on that lattice. The vector clock is stored
    with the payload: it is the causality evidence, and dropping it would leave
    a durable record that cannot be ordered.
    """
    memory = _memory()
    topic = f"lattice.{lattice}.{event['type']}"
    return memory.remember(
        topic=topic,
        content=json.dumps(
            {
                "id": event["id"],
                "source": event.get("source"),
                "ts": event.get("ts"),
                "vector": event.get("vector", {}),
                "parent": event.get("parent"),
                "payload": event.get("payload"),
            },
            sort_keys=True,
        ),
        tags=["lattice", lattice, event["type"]],
        actor=actor,
        epistemic_status="observed",
        source=f"mem20crossruntimeeventlatticez:{lattice}",
    )


def recall_events(lattice: str, event_type: str | None = None) -> list[dict]:
    """Read back the events persisted for a lattice (optionally one type)."""
    memory = _memory()
    topic = f"lattice.{lattice}" + (f".{event_type}" if event_type else "")
    return memory.recall(topic=topic)


def memory_status() -> str:
    """The engine's own status report — a health signal for the CLI."""
    return _memory().status()


# --------------------------------------------------------------------------
# memory_engine.retrieval_v2 — multi-hop search over lattice history
# --------------------------------------------------------------------------


def search_history(query: str, k: int = 5) -> dict:
    """Decompose a compound question about the lattice into sub-retrievals.

    "which runtime emitted the first failure and what did it cause" is two
    questions; ``decompose_query`` splits and runs each.
    """
    os.environ.setdefault("MEM20_STORE_PATH", store_path())
    retrieval = _live(_retrieval, "memory_engine.retrieval_v2", "memory_engine")
    return retrieval.decompose_query(query, k=k)


# --------------------------------------------------------------------------
# toolchest — capability inventory
# --------------------------------------------------------------------------


def capability_inventory() -> dict:
    """The estate's measured tool inventory.

    A lattice only advertises a runtime it can actually reach, so the inventory
    is the measured list rather than a configured one.
    """
    catalog = _need(_catalog, "toolchest.catalog", "toolchest")
    return catalog.load_inventory(REPO_ROOT / "toolchest" / "inventory.json")


def inventory_counts() -> dict:
    """Just the counts block — cheap enough for a health response."""
    return dict(capability_inventory().get("counts", {}))


# --------------------------------------------------------------------------
# gateway — fleet announcement
# --------------------------------------------------------------------------


def announce(event: dict, *, lattice: str = "default", agent_name: str | None = None) -> dict:
    """Announce a lattice event to the mem20 fleet gateway.

    ``broadcast`` writes a real line to the gateway's message log and returns
    the entry. It exits the process when no agent is registered, so the name is
    registered first if the gateway does not know it.
    """
    gateway = _need(_gateway, "gateway.hermes_gateway", "gateway")
    name = agent_name or f"lattice-{lattice}"
    if name not in gateway.load_names():
        gateway.register_agent(name=name, location="mem20crossruntimeeventlatticez")
    return gateway.broadcast(
        f"{event['type']} id={event['id']} source={event.get('source')}",
        agent_name=name,
        target="lattice",
    )


def fleet_messages(limit: int = 20) -> list[dict]:
    """Read back what the fleet has announced, newest first.

    Reads the gateway's own message log (``hermes_gateway.MESSAGES_FILE``), the
    file ``broadcast`` appends to.

    ``hermes_gateway.read_messages`` is deliberately not used: it indexes
    ``m["agent"]`` while ``broadcast`` writes ``agent_name``, so it raises
    ``KeyError: 'agent'`` on every message the gateway itself produced. That is
    a defect in the gateway subsystem (owned by the Server Builder wave-1
    module); writing a different field name here would make the two writers
    disagree, so the log is read directly until the gateway is fixed.
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
# mem20verify / mem20ops — integrity of the lattice record
# --------------------------------------------------------------------------


def verify_memory_integrity() -> dict:
    """Round-trip the memory engine and report whether the ledger is faithful.

    This is what makes a persisted lattice history usable as evidence: it
    writes known payloads through ``remember`` and compares what was stored.
    """
    dataintegrity = _need(_dataintegrity, "mem20verify.dataintegrity", "mem20verify")

    # ``check()`` imports ``memory`` and rebinds ``ENTRIES``/``LEDGER`` on that
    # module object to a temp dir. The repo root also ships a ``memory.py``
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
# mem20corez — compact a lattice payload for the wire
# --------------------------------------------------------------------------


def compact_payload(values: list[float], bits: int = 8) -> dict:
    """Quantize a numeric payload before it crosses a runtime boundary.

    Real quantization from mem20corez, with the measured reconstruction error so
    a caller can decide whether the compression is acceptable for its lattice.
    ``QuantizedTensor`` exposes ``.q`` / ``.scale`` fields (no ``dequantize()``
    method), so the reconstruction is done here.
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
# the composed path — what the README example and the CLI both run
# --------------------------------------------------------------------------


def emit_and_record(
    event_type: str,
    payload: dict,
    *,
    lattice: str = "default",
    source: str = "local",
    parent: dict | None = None,
    announce_to_fleet: bool = True,
) -> dict:
    """Emit an event, link it causally, persist it, and announce it.

    The one call that exercises the whole seam: domain emission and causality,
    durable memory, and the fleet gateway. Every real result is returned so a
    caller can assert on it rather than trusting a boolean.
    """
    event = domain.emit(event_type, payload, source=source)
    if parent is not None:
        event = domain.causal_link(parent, event)
    record = remember_event(event, lattice=lattice)
    out: dict[str, Any] = {
        "event": event,
        "memory_id": record.get("id"),
        "memory_topic": record.get("topic"),
        "announced": None,
    }
    if announce_to_fleet:
        out["announced"] = announce(event, lattice=lattice)
    return out


def lattice_report(lattices: list[dict], *, name: str = "default", window_s: int = 60) -> dict:
    """A real operational report for a merged lattice.

    Combines the domain's own merge/order result with the estate's inventory
    counts and the memory engine's status, so an operator sees the lattice and
    the substrate it depends on in one object.
    """
    merged = domain.lattice_merge(lattices)
    events = merged["events"]
    by_type: dict[str, int] = {}
    for e in events:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    sources = sorted({e.get("source") for e in events})
    status = memory_status()
    return {
        "lattice": name,
        "count": merged["count"],
        "by_type": by_type,
        "sources": sources,
        "causal_links": sum(1 for e in events if e.get("parent")),
        "span_s": round((events[-1]["ts"] - events[0]["ts"]), 6) if len(events) > 1 else 0.0,
        "inventory": inventory_counts(),
        "memory": status.splitlines()[0] if status else "",
        "generated_at": time.time(),
    }
