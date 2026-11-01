"""MCP tools for the bi-temporal store (mem20temporaldatabasefabricz).

Registration is two-part by design:

* ``TOOLS`` is the declarative list the MCP server reads to expose these to a
  client.
* ``install(server)`` performs the actual registration against a live server
  object.

A tools file that is only imported - or only listed - changes nothing, which is
why the branch also calls ``install`` from ``mcp/server.py`` and a test asserts
the tools are reachable through it.

Every handler here goes through the subsystem's real engine, so a tool call
exercises the same estate wiring the tests do.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["TOOLS", "install", "handle"]

# <repo>/mcp/tools/temporal_tools.py -> <repo>
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "mem20temporaldatabasefabricz" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _store():
    """Open the temporal store at the configured path."""
    from mem20temporaldatabasefabricz.temporal.store import TemporalStore

    path = os.environ.get(
        "MEM20_TEMPORAL_DB",
        str(Path(os.environ.get("MEM20_STORE_PATH", Path.home() / ".mem20"))
            / "temporal" / "temporal.db"))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return TemporalStore(path)


def _engine(store):
    from mem20temporaldatabasefabricz.temporal.engine import BiTemporalEngine

    return BiTemporalEngine(store)


def temporal_put(subject: str, attribute: str, value_ref: str,
                 valid_from: str | None = None,
                 known_at: str | None = None) -> dict:
    """Record a belief about a subject. Refused if the value is a credential."""
    store = _store()
    try:
        interval = _engine(store).assert_belief(
            subject, attribute, value_ref, valid_from=valid_from, known_at=known_at)
        return {"ok": True, "version_id": interval.version_id,
                "valid_from": interval.valid_from, "known_from": interval.known_from,
                "provenance": interval.provenance}
    finally:
        store.close()


def temporal_get(subject: str, valid_at: str | None = None,
                 known_at: str | None = None) -> dict:
    """What was true at valid_at, as far as the system knew at known_at."""
    store = _store()
    try:
        result = _engine(store).query(subject, valid_at=valid_at, known_at=known_at)
        return {"found": bool(len(result)), "subject": subject,
                "count": len(result),
                "values": result.value_refs(),
                "rows": [i.to_dict() for i in result]}
    finally:
        store.close()


def temporal_slices(subject: str, at: str) -> dict:
    """All four bi-temporal slices for a subject at one instant."""
    store = _store()
    try:
        return _engine(store).four_slices(subject, at)
    finally:
        store.close()


def temporal_ingest(ledger_path: str | None = None, verify: bool = True) -> dict:
    """Ingest the memory ledger, after the estate verifies it can round-trip."""
    from mem20temporaldatabasefabricz.temporal.ledger_adapter import ingest_ledger

    store = _store()
    try:
        return ingest_ledger(store, ledger_path, verify=verify)
    finally:
        store.close()


def temporal_doctor() -> dict:
    """Report which estate projects this subsystem is wired to, and probe them."""
    from mem20temporaldatabasefabricz.temporal import estate

    return {
        "estate": estate.estate_status(),
        "wire_classifier": estate.wire_noise(),
        "inventory": estate.tool_inventory(limit=3),
        "sample_identity": estate.identity(),
    }


TOOLS = [
    {
        "name": "temporal_put",
        "description": "Record a belief in the bi-temporal store (refuses "
                       "credentials: the store is append-only).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "exact subject/topic"},
                "attribute": {"type": "string"},
                "value_ref": {"type": "string", "description": "reference to the value"},
                "valid_from": {"type": "string", "description": "ISO-8601 event time"},
                "known_at": {"type": "string", "description": "ISO-8601 system time"},
            },
            "required": ["subject", "attribute", "value_ref"],
        },
        "handler": temporal_put,
    },
    {
        "name": "temporal_get",
        "description": "Read a subject through a bi-temporal slice.",
        "inputSchema": {
            "type": "object",
            "properties": {"subject": {"type": "string"},
                           "valid_at": {"type": "string"},
                           "known_at": {"type": "string"}},
            "required": ["subject"],
        },
        "handler": temporal_get,
    },
    {
        "name": "temporal_slices",
        "description": "All four slices (current, as-of, historical, conflict) "
                       "for a subject at one instant.",
        "inputSchema": {
            "type": "object",
            "properties": {"subject": {"type": "string"}, "at": {"type": "string"}},
            "required": ["subject", "at"],
        },
        "handler": temporal_slices,
    },
    {
        "name": "temporal_ingest",
        "description": "Ingest mem20's memory ledger into the temporal store, "
                       "after mem20verify confirms the ledger round-trips.",
        "inputSchema": {
            "type": "object",
            "properties": {"ledger_path": {"type": "string"},
                           "verify": {"type": "boolean", "default": True}},
        },
        "handler": temporal_ingest,
    },
    {
        "name": "temporal_doctor",
        "description": "Probe the estate projects the temporal store is wired to.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": temporal_doctor,
    },
]

_BY_NAME = {tool["name"]: tool["handler"] for tool in TOOLS}


def handle(name: str, arguments: dict | None = None) -> dict:
    """Dispatch a tool call by name. Raises KeyError for an unknown tool."""
    handler = _BY_NAME[name]
    return handler(**(arguments or {}))


def install(server) -> list[str]:
    """Register every tool on a live MCP server object.

    Accepts either a ``register``-style method (``server.register(name, desc,
    schema, handler)``) or a plain dict registry (``server.tools[name] = tool``),
    because the estate's servers use both. Returns the names registered, so the
    caller (and a test) can assert the tools actually reached the server.
    """
    registered: list[str] = []
    for tool in TOOLS:
        if hasattr(server, "register"):
            server.register(tool["name"], tool["description"],
                            tool["inputSchema"], tool["handler"])
        elif isinstance(getattr(server, "tools", None), dict):
            server.tools[tool["name"]] = {
                "name": tool["name"], "description": tool["description"],
                "inputSchema": tool["inputSchema"], "handler": tool["handler"],
            }
        else:  # pragma: no cover - server contract changed
            raise TypeError(
                f"cannot register MCP tools on {type(server).__name__}: it has "
                f"neither register() nor a tools dict")
        registered.append(tool["name"])
    return registered
