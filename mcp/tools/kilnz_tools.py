"""mem20kilnz MCP tools — the asset build gate.

Exposes the kiln's pre-build/post-build gate to any MCP host. Every tool routes
through ``mem20kilnz.ecosystem``, so a call from a client exercises the same
cross-subsystem wiring the tests do: grounded recall from ``memory_engine``, the
epistemic veto from ``mem20crewz``, AST checks from ``mem20verify``, fidelity
from ``mem20dreamz`` and the char-MLP perplexity from ``mem20corez``.

Tools:

- ``kilnz_status``   — is the kiln importable, and what does it wire to
- ``kilnz_ground``   — grounded context about an asset family before a build
- ``kilnz_gate``     — judge a build result before the asset ships
- ``kilnz_budget``   — check a triangle count against the authored budget table

The import is lazy and guarded: a host that has not installed the kiln still
gets ``kilnz_status`` reporting the absence, rather than a server that fails to
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

#: The subsystems this surface depends on, in the order a build uses them.
KILNZ_SUBSYSTEMS = (
    "memory_engine", "mem20crewz", "mem20verify", "mem20dreamz", "mem20corez",
    "mem20cliz",
)


def _ecosystem():
    """Import mem20kilnz.ecosystem, preferring the project directory.

    The estate layout is ``<repo>/mem20kilnz/mem20kilnz/``, so the repo root
    alone resolves the *outer* directory as a namespace package. Put the project
    directory first so the real package wins.
    """
    project = os.path.join(_REPO_ROOT, "mem20kilnz")
    if project not in sys.path:
        sys.path.insert(0, project)
    from mem20kilnz import ecosystem  # type: ignore[import-not-found]
    return ecosystem


class KilnzToolsMixin:
    """mem20kilnz tools for the mem20 MCP server."""

    def register_kilnz_tools(self):
        self.tools["kilnz_status"] = mt.Tool(
            name="kilnz_status",
            title="Kiln Status",
            description=(
                "Report whether the mem20kilnz asset kiln is importable and "
                "which mem20 subsystems its build gate wires to."
            ),
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["kilnz_ground"] = mt.Tool(
            name="kilnz_ground",
            title="Ground a Build",
            description=(
                "Read grounded facts about an asset family before a build. "
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
        self.tools["kilnz_gate"] = mt.Tool(
            name="kilnz_gate",
            title="Judge a Build Result",
            description=(
                "Judge a build result before the asset ships: epistemic veto "
                "(mem20crewz), AST lint (mem20verify), fidelity/divergence "
                "(mem20dreamz) and corpus distance (mem20corez), grounded "
                "against memory_engine. Returns a per-subsystem report and a "
                "shippable verdict."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "brief": {"type": "string", "description": "The build brief"},
                    "result": {"type": "string", "description": "The build result"},
                    "topic": {"type": "string", "description": "Memory topic"},
                    "record": {"type": "boolean", "default": False,
                               "description": "Append the build to the ledger"},
                },
                "required": ["brief", "result"],
            },
        )
        self.tools["kilnz_budget"] = mt.Tool(
            name="kilnz_budget",
            title="Check a Triangle Budget",
            description=(
                "Check a triangle count against the authored budget table for an "
                "asset family, at a detail tier and LOD."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "family": {"type": "string", "description": "Asset family"},
                    "triangles": {"type": "integer"},
                    "lod": {"type": "integer", "default": 0},
                    "tier": {"type": "string", "default": "standard"},
                },
                "required": ["family", "triangles"],
            },
        )

    # ------------------------------------------------------------- handlers
    async def _kilnz_status(self, args: Dict[str, Any]) -> str:
        try:
            _ecosystem()
        except Exception as exc:  # noqa: BLE001
            return json.dumps({"ok": False, "available": False,
                               "error": f"{type(exc).__name__}: {exc}"}, indent=2)
        return json.dumps({
            "ok": True, "available": True,
            "subsystems": list(KILNZ_SUBSYSTEMS),
            "gate": "BuildGate(prepare -> judge)",
        }, indent=2)

    async def _kilnz_ground(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        return json.dumps(
            eco.grounded_context(topic=args.get("topic"),
                                 k=int(args.get("k", 5))), indent=2)

    async def _kilnz_gate(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        out = eco.run_gate(
            brief=args.get("brief", ""),
            result=args.get("result", ""),
            topic=args.get("topic"),
            record=bool(args.get("record", False)),
        )
        return json.dumps(out, indent=2)

    async def _kilnz_budget(self, args: Dict[str, Any]) -> str:
        project = os.path.join(_REPO_ROOT, "mem20kilnz")
        if project not in sys.path:
            sys.path.insert(0, project)
        from mem20kilnz import budgets  # type: ignore[import-not-found]

        verdict = budgets.check_triangles(
            args.get("family", ""), int(args.get("triangles", 0)),
            lod=int(args.get("lod", 0)), tier=args.get("tier", "standard"))
        return json.dumps(verdict.as_dict(), indent=2)
