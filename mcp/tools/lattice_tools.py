"""MCP tools for the cross-runtime event lattice.

Thin by design: emission, causality, persistence and verification all live in
the subsystem's ``domain`` and ``integration`` modules. These tools are a door
onto that code so an agent can emit a causally-linked event, read a merged
lattice's report, or verify the audit trail without shelling out.

The descriptions carry the two things an agent needs in order not to waste
tokens: ``lattice_emit`` returns the event id and its vector clock (so a later
``lattice_emit`` can pass it as ``parent``), and ``lattice_report`` already
includes substrate health, so there is no second call to make.
"""
import json
from typing import Any, Dict

try:
    from mcp.server import Server
    from mcp.server.lowlevel.server import ServerRequestContext
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
    MCP_SDK_IMPORT_ERROR = None
except ImportError as _mcp_sdk_exc:  # pragma: no cover - only without the SDK
    # Never sys.exit() at import time: pytest imports this module during
    # collection and a SystemExit aborts the whole session instead of
    # reporting one collection error. Full note in mcp/server.py.
    MCP_SDK_AVAILABLE = False
    MCP_SDK_IMPORT_ERROR = _mcp_sdk_exc


class LatticeToolsMixin:
    """MCP tools exposing the cross-runtime event lattice."""

    def register_lattice_tools(self):
        self.tools["lattice_emit"] = mt.Tool(
            name="lattice_emit",
            title="Emit Lattice Event",
            description=(
                "Emit a typed event on a lattice, optionally link it causally to "
                "a parent event, persist it to durable memory and announce it to "
                "the mem20 fleet. Returns the event (with its id and vector "
                "clock), the memory id, and the gateway entry. Pass the returned "
                "event id as `parent` on a later call to extend the causal chain."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Event type, e.g. session.view."},
                    "payload": {"type": "object", "description": "Event payload."},
                    "lattice": {"type": "string", "description": "Lattice name."},
                    "source": {"type": "string", "description": "Emitting runtime: local, edge or cloud."},
                    "parent": {"type": "string", "description": "Parent event id to link causally."},
                    "announce": {"type": "boolean", "default": True},
                },
                "required": ["type"],
            },
        )
        self.tools["lattice_report"] = mt.Tool(
            name="lattice_report",
            title="Lattice Report",
            description=(
                "Operational report for a merged lattice: event count, counts by "
                "type, contributing runtimes, causal-link count, time span, plus "
                "the estate's measured inventory counts and memory-engine "
                "status. One call answers both 'is the lattice healthy' and 'is "
                "the substrate healthy'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lattice": {"type": "string"},
                    "lattices": {
                        "type": "array",
                        "description": "Lattices to merge, each {\"events\": [...]}.",
                        "items": {"type": "object"},
                    },
                },
                "required": [],
            },
        )
        self.tools["lattice_recall"] = mt.Tool(
            name="lattice_recall",
            title="Recall Lattice Events",
            description=(
                "Read back the events persisted for a lattice, optionally "
                "narrowed to one event type. Returns the ledger rows the lattice "
                "wrote, including each event's vector clock and parent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lattice": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["lattice"],
            },
        )
        self.tools["lattice_verify"] = mt.Tool(
            name="lattice_verify",
            title="Verify Lattice Audit Trail",
            description=(
                "Round-trip the memory engine and report whether the ledger "
                "faithfully stored what was written. Use before treating a "
                "recalled lattice history as evidence."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        self.tools["lattice_search"] = mt.Tool(
            name="lattice_search",
            title="Search Lattice History",
            description=(
                "Answer a compound causality question by decomposing it into "
                "sub-retrievals. Use for questions that ask two things at once, "
                "e.g. 'which runtime emitted the first failure and what did it "
                "cause'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        )

    # ------------------------------------------------------------- handlers
    def _lattice(self):
        from mem20crossruntimeeventlatticez import domain, integration

        return domain, integration

    async def _lattice_emit(self, args: Dict[str, Any]) -> str:
        domain, integration = self._lattice()
        parent = None
        if args.get("parent"):
            parent = domain.emit("parent", {}, source=args.get("source", "local"))
            parent["id"] = args["parent"]
        out = integration.emit_and_record(
            args["type"],
            args.get("payload") or {},
            lattice=args.get("lattice") or "default",
            source=args.get("source") or "local",
            parent=parent,
            announce_to_fleet=bool(args.get("announce", True)),
        )
        return json.dumps(out, indent=2, sort_keys=True, default=str)

    async def _lattice_report(self, args: Dict[str, Any]) -> str:
        _, integration = self._lattice()
        return json.dumps(
            integration.lattice_report(
                args.get("lattices") or [],
                name=args.get("lattice") or "default",
            ),
            indent=2,
            sort_keys=True,
            default=str,
        )

    async def _lattice_recall(self, args: Dict[str, Any]) -> str:
        _, integration = self._lattice()
        rows = integration.recall_events(args["lattice"], args.get("type"))
        return json.dumps(rows, indent=2, sort_keys=True, default=str)

    async def _lattice_verify(self, args: Dict[str, Any]) -> str:
        _, integration = self._lattice()
        return json.dumps(integration.verify_memory_integrity(), indent=2, sort_keys=True)

    async def _lattice_search(self, args: Dict[str, Any]) -> str:
        _, integration = self._lattice()
        return json.dumps(
            integration.search_history(args["query"], k=int(args.get("k", 5))),
            indent=2,
            sort_keys=True,
            default=str,
        )
