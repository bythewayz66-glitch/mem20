"""Memory Engine 4.0 substrate tools for the mem20 MCP server.

These expose the ``memory_engine.substrate`` public API to MCP clients so an
agent can ask the substrate's questions directly instead of re-deriving them:

- ``memory_engine_health``      ledger counts, label coverage, retrieval halves
- ``memory_engine_recall``      recall with the epistemic label intact
- ``memory_engine_veto``        may a plan rest on these fact ids?
- ``memory_engine_guard``       the same question through mem20crewz guardrails
- ``memory_engine_namespace``   the memory namespace an agent owns
- ``memory_engine_subsystem``   is a subsystem installed, and what does it expose?

Registration is real: ``register_memory_engine_tools`` puts each tool in
``self.tools`` and each handler is ``_<tool_name>``, which is the convention
``Mem20MCPServer._execute_tool`` dispatches on. A tool that is registered but
has no handler is reported as an error by the server rather than silently
doing nothing.
"""

from __future__ import annotations

import json
import os
import sys
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


def _substrate():
    """Import the substrate, making the repo root importable first.

    The MCP server may be started from any cwd; the substrate lives at
    ``<repo>/memory_engine/substrate.py``.
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from memory_engine import substrate

    return substrate


class MemoryEngineToolsMixin:
    """memory_engine 4.0 substrate tools for mem20."""

    def register_memory_engine_tools(self):
        """Register the memory_engine substrate tools."""
        if not MCP_SDK_AVAILABLE:
            return

        self.tools["memory_engine_health"] = mt.Tool(
            name="memory_engine_health",
            title="Memory Engine Health",
            description=(
                "Report the memory engine's real state: ledger event count, "
                "grounded fact count, epistemic label coverage, and which "
                "retrieval halves (vector / BM25) are actually installed. "
                "Every figure is measured from the store, not estimated."
            ),
            inputSchema={"type": "object", "properties": {}},
        )

        self.tools["memory_engine_recall"] = mt.Tool(
            name="memory_engine_recall",
            title="Memory Engine Recall",
            description=(
                "Recall facts from the memory engine with the epistemic label "
                "intact on every row. A row with no recorded basis is returned "
                "as 'unlabeled' rather than with the field absent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic filter"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tag filter (any match)",
                    },
                    "k": {"type": "integer", "default": 5},
                    "include_simulated": {
                        "type": "boolean",
                        "default": False,
                        "description": "Also surface active simulated records",
                    },
                },
            },
        )

        self.tools["memory_engine_veto"] = mt.Tool(
            name="memory_engine_veto",
            title="Memory Engine Epistemic Veto",
            description=(
                "Ask whether a plan may rest on these fact ids. Returns the "
                "engine's verdict: vetoed or not, the offending ids, and any "
                "ids that resolve to nothing (a typo is reported, not ignored)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fact_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fact ids the plan relies on",
                    },
                    "actor": {"type": "string", "default": "agent"},
                },
                "required": ["fact_ids"],
            },
        )

        self.tools["memory_engine_guard"] = mt.Tool(
            name="memory_engine_guard",
            title="Memory Engine Plan Guard",
            description=(
                "Run the same trust question through mem20crewz's guardrail "
                "bundle (plan-execution gate + epistemic clearance), so a crew "
                "and a direct caller cannot disagree about whether a plan runs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fact_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "actor": {"type": "string", "default": "agent"},
                },
                "required": ["fact_ids"],
            },
        )

        self.tools["memory_engine_namespace"] = mt.Tool(
            name="memory_engine_namespace",
            title="Memory Engine Namespace",
            description=(
                "Return the memory namespace an agent owns, using mem20agentz's "
                "naming rule so the agent platform and a direct caller agree."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "description": "Agent name"},
                },
                "required": ["agent"],
            },
        )

        self.tools["memory_engine_subsystem"] = mt.Tool(
            name="memory_engine_subsystem",
            title="Memory Engine Subsystem Status",
            description=(
                "Report whether a named mem20 subsystem is installed and what it "
                "exposes, read from toolchest's on-disk catalogue. A renamed or "
                "removed subsystem shows up as absent."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Subsystem directory name"},
                },
                "required": ["name"],
            },
        )

    # ------------------------------------------------------------------
    # handlers — the _<tool_name> convention _execute_tool dispatches on
    # ------------------------------------------------------------------
    async def _memory_engine_health(self, args: Dict[str, Any]) -> str:
        return json.dumps(_substrate().health(), indent=2, sort_keys=True, default=str)

    async def _memory_engine_recall(self, args: Dict[str, Any]) -> str:
        rows = _substrate().recall_facts(
            args.get("topic"),
            tags=args.get("tags") or None,
            k=int(args.get("k", 5)),
            include_simulated=bool(args.get("include_simulated", False)),
        )
        return json.dumps(rows, indent=2, sort_keys=True, default=str)

    async def _memory_engine_veto(self, args: Dict[str, Any]) -> str:
        verdict = _substrate().veto_plan(
            args.get("fact_ids") or [], actor=args.get("actor", "agent"))
        return json.dumps(verdict, indent=2, sort_keys=True, default=str)

    async def _memory_engine_guard(self, args: Dict[str, Any]) -> str:
        result = _substrate().guard_plan(
            args.get("fact_ids") or [], actor=args.get("actor", "agent"))
        return json.dumps(result, indent=2, sort_keys=True, default=str)

    async def _memory_engine_namespace(self, args: Dict[str, Any]) -> str:
        agent = args.get("agent", "")
        return json.dumps(
            {"agent": agent, "namespace": _substrate().namespace_for_agent(agent)},
            indent=2, sort_keys=True)

    async def _memory_engine_subsystem(self, args: Dict[str, Any]) -> str:
        return json.dumps(
            _substrate().subsystem_status(args.get("name", "")),
            indent=2, sort_keys=True, default=str)
