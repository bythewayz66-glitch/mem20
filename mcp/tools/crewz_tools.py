"""mem20crewz MCP tools — the crew governance surface.

Exposes the crew runtime's pre-flight/post-flight governor to any MCP host.
Every tool routes through ``mem20crewz.ecosystem``, so a call from a client
exercises the same cross-subsystem wiring the tests do: grounded recall from
``memory_engine``, AST checks from ``mem20verify``, fidelity from
``mem20dreamz``, asset budgets from ``mem20kilnz`` and the char-MLP perplexity
from ``mem20corez``.

Tools:

- ``crewz_status``   — is the crew runtime importable, and what does it wire to
- ``crewz_ground``   — grounded context before a crew starts
- ``crewz_govern``   — judge a crew output before it ships (all five subsystems)
- ``crewz_guard``    — the crew's own epistemic veto over a set of fact ids

The import is lazy and guarded: a host that has not installed the runtime still
gets ``crewz_status`` reporting the absence, rather than a server that fails to
start.
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

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

#: The subsystems this surface depends on, in the order a crew run uses them.
CREWZ_SUBSYSTEMS = (
    "memory_engine", "mem20verify", "mem20dreamz", "mem20kilnz", "mem20corez",
    "mem20cliz",
)


def _ecosystem():
    """Import mem20crewz.ecosystem, preferring the project directory.

    The estate layout is ``<repo>/mem20crewz/ecosystem.py`` (flat), but the repo
    root alone lets ``import mem20crewz`` resolve the outer directory first. Put
    the project directory first so the module under it wins.
    """
    project = os.path.join(_REPO_ROOT, "mem20crewz")
    if project not in sys.path:
        sys.path.insert(0, project)
    import ecosystem  # type: ignore[import-not-found]
    return ecosystem


class CrewzToolsMixin:
    """mem20crewz tools for the mem20 MCP server."""

    def register_crewz_tools(self):
        self.tools["crewz_status"] = mt.Tool(
            name="crewz_status",
            title="Crew Runtime Status",
            description=(
                "Report whether the mem20crewz crew runtime is importable and "
                "which mem20 subsystems its governor wires to."
            ),
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["crewz_ground"] = mt.Tool(
            name="crewz_ground",
            title="Ground a Crew",
            description=(
                "Read grounded facts a crew should know before it starts. "
                "Simulated content is excluded by memory_engine's firewall."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Memory topic"},
                    "k": {"type": "integer", "default": 5},
                },
            },
        )
        self.tools["crewz_govern"] = mt.Tool(
            name="crewz_govern",
            title="Govern a Crew Output",
            description=(
                "Judge a crew output before it ships: AST lint (mem20verify), "
                "fidelity/divergence (mem20dreamz), asset budget (mem20kilnz) "
                "and corpus distance (mem20corez), grounded against "
                "memory_engine. Returns a per-subsystem report and a clear "
                "verdict."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "brief": {"type": "string", "description": "The task brief"},
                    "output": {"type": "string", "description": "The crew output"},
                    "topic": {"type": "string", "description": "Memory topic"},
                    "triangles": {"type": "integer",
                                  "description": "Claimed triangle count, if any"},
                    "record": {"type": "boolean", "default": False,
                               "description": "Append the outcome to the ledger"},
                },
                "required": ["brief", "output"],
            },
        )
        self.tools["crewz_guard"] = mt.Tool(
            name="crewz_guard",
            title="Crew Epistemic Veto",
            description=(
                "Run the crew's own epistemic veto over a set of fact ids: may a "
                "plan rest on these facts, given their labels."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "fact_ids": {"type": "array", "items": {"type": "string"},
                                 "description": "Fact ids to check"},
                    "actor": {"type": "string", "default": "mcp"},
                },
                "required": ["fact_ids"],
            },
        )

    # ------------------------------------------------------------- handlers
    async def _crewz_status(self, args: Dict[str, Any]) -> str:
        try:
            _ecosystem()
        except Exception as exc:  # noqa: BLE001
            return json.dumps({"ok": False, "available": False,
                               "error": f"{type(exc).__name__}: {exc}"}, indent=2)
        return json.dumps({
            "ok": True, "available": True,
            "subsystems": list(CREWZ_SUBSYSTEMS),
            "governor": "CrewGovernor(prepare -> judge)",
        }, indent=2)

    async def _crewz_ground(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        return json.dumps(
            eco.grounded_context(topic=args.get("topic"),
                                 k=int(args.get("k", 5))), indent=2)

    async def _crewz_govern(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        out = eco.run_governor(
            brief=args.get("brief", ""),
            output=args.get("output", ""),
            topic=args.get("topic"),
            triangles=args.get("triangles"),
            record=bool(args.get("record", False)),
        )
        return json.dumps(out, indent=2)

    async def _crewz_guard(self, args: Dict[str, Any]) -> str:
        project = os.path.join(_REPO_ROOT, "mem20crewz")
        if project not in sys.path:
            sys.path.insert(0, project)
        from mem20crewz import guardrails  # type: ignore[import-not-found]

        guards = guardrails.Guards(actor=args.get("actor", "mcp"),
                                   enforce_plan=False, sweep_after=False)
        return json.dumps(
            guards.check_clearance(list(args.get("fact_ids") or [])), indent=2)
