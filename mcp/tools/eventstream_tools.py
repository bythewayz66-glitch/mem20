"""MCP tools for the event stream superhighway.

Thin by design: the routing, persistence and verification all live in the
subsystem's ``domain`` and ``integration`` modules. These tools are a door onto
that code so an agent can publish an event, read a stream's operational report,
or verify the audit trail without shelling out.

The tool descriptions carry the two things an agent needs in order not to waste
tokens: ``stream_publish`` returns the memory id it wrote (so a later
``stream_recall`` is one cheap call), and ``stream_report`` already includes the
substrate health, so there is no second call to make.
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


class EventStreamToolsMixin:
    """MCP tools exposing the event stream superhighway."""

    def register_eventstream_tools(self):
        self.tools["stream_publish"] = mt.Tool(
            name="stream_publish",
            title="Publish Event",
            description=(
                "Publish a typed event to a stream, persist it to durable memory "
                "and announce it to the mem20 fleet. Returns the event, the "
                "memory id it was written under, and the gateway entry. Use the "
                "returned memory_topic with stream_recall to read it back."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stream": {"type": "string", "description": "Stream name."},
                    "type": {"type": "string", "description": "Event type, e.g. order.created."},
                    "payload": {"type": "object", "description": "Event payload."},
                    "key": {"type": "string", "description": "Optional partition key."},
                    "announce": {"type": "boolean", "default": True},
                },
                "required": ["type"],
            },
        )
        self.tools["stream_report"] = mt.Tool(
            name="stream_report",
            title="Stream Report",
            description=(
                "Operational report for a stream: event count, subscribers, "
                "throughput per minute, per-subscriber lag, plus the estate's "
                "measured inventory counts and memory-engine status. One call "
                "answers both 'is the stream healthy' and 'is the substrate "
                "healthy'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stream": {"type": "string"},
                    "window_s": {"type": "integer", "default": 60},
                },
                "required": [],
            },
        )
        self.tools["stream_recall"] = mt.Tool(
            name="stream_recall",
            title="Recall Stream Events",
            description=(
                "Read back the events persisted for a stream, optionally "
                "narrowed to one event type. Returns the ledger rows the "
                "superhighway wrote, newest last."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "stream": {"type": "string"},
                    "type": {"type": "string"},
                },
                "required": ["stream"],
            },
        )
        self.tools["stream_verify"] = mt.Tool(
            name="stream_verify",
            title="Verify Event Audit Trail",
            description=(
                "Round-trip the memory engine and report whether the ledger "
                "faithfully stored what was written. Use before trusting a "
                "recall result for an audit or a report."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        self.tools["stream_search"] = mt.Tool(
            name="stream_search",
            title="Search Stream Telemetry",
            description=(
                "Answer a compound question about the stream by decomposing it "
                "into sub-retrievals. Use for questions that ask two things at "
                "once, e.g. 'what is the p95 latency and which partition is hot'."
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
    def _eventstream(self):
        from mem20eventstreamsuperhighwayz import domain, integration

        return domain, integration

    async def _stream_publish(self, args: Dict[str, Any]) -> str:
        domain, integration = self._eventstream()
        stream = domain.create_stream(args.get("stream") or "default")
        out = integration.publish_and_persist(
            stream,
            args["type"],
            args.get("payload") or {},
            key=args.get("key"),
            announce_to_fleet=bool(args.get("announce", True)),
        )
        return json.dumps(out, indent=2, sort_keys=True, default=str)

    async def _stream_report(self, args: Dict[str, Any]) -> str:
        domain, integration = self._eventstream()
        stream = domain.create_stream(args.get("stream") or "default")
        return json.dumps(
            integration.stream_report(stream, window_s=int(args.get("window_s", 60))),
            indent=2,
            sort_keys=True,
            default=str,
        )

    async def _stream_recall(self, args: Dict[str, Any]) -> str:
        _, integration = self._eventstream()
        rows = integration.recall_events(args["stream"], args.get("type"))
        return json.dumps(rows, indent=2, sort_keys=True, default=str)

    async def _stream_verify(self, args: Dict[str, Any]) -> str:
        _, integration = self._eventstream()
        return json.dumps(integration.verify_memory_integrity(), indent=2, sort_keys=True)

    async def _stream_search(self, args: Dict[str, Any]) -> str:
        _, integration = self._eventstream()
        return json.dumps(
            integration.search_events(args["query"], k=int(args.get("k", 5))),
            indent=2,
            sort_keys=True,
            default=str,
        )
