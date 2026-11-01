"""mem20dreamz MCP tools — the dream promotion gate.

Exposes the dream engine's gate to any MCP host. Every tool routes through
``mem20dreamz.ecosystem``, so a call from a client exercises the same
cross-subsystem wiring the tests do: grounded recall from ``memory_engine``, the
epistemic veto from ``mem20crewz``, AST checks from ``mem20verify``, asset
budgets from ``mem20kilnz`` and the char-MLP perplexity from ``mem20corez``.

Tools:

- ``dreamz_status``  — is the dream engine importable, and what does it wire to
- ``dreamz_ground``  — what the estate already knows about a seed
- ``dreamz_gate``    — judge a candidate before promotion (all five subsystems)
- ``dreamz_estate``  — installed vs claimed vs phantom subsystems

The import is lazy and guarded: a host that has not installed the engine still
gets ``dreamz_status`` reporting the absence, rather than a server that fails to
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

#: The subsystems this surface depends on, in the order a dream uses them.
DREAMZ_SUBSYSTEMS = (
    "memory_engine", "mem20crewz", "mem20verify", "mem20kilnz", "mem20corez",
    "mem20cliz",
)


def _ecosystem():
    """Import mem20dreamz.ecosystem, preferring the project directory.

    The estate layout is ``<repo>/mem20dreamz/mem20dreamz/``, so the repo root
    alone resolves the *outer* directory as a namespace package. Put the project
    directory first so the real package wins.
    """
    project = os.path.join(_REPO_ROOT, "mem20dreamz")
    if project not in sys.path:
        sys.path.insert(0, project)
    from mem20dreamz import ecosystem  # type: ignore[import-not-found]
    return ecosystem


class DreamzToolsMixin:
    """mem20dreamz tools for the mem20 MCP server."""

    def register_dreamz_tools(self):
        self.tools["dreamz_status"] = mt.Tool(
            name="dreamz_status",
            title="Dream Engine Status",
            description=(
                "Report whether the mem20dreamz dream engine is importable and "
                "which mem20 subsystems its promotion gate wires to."
            ),
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["dreamz_ground"] = mt.Tool(
            name="dreamz_ground",
            title="Ground a Dream Seed",
            description=(
                "Read what the estate already knows about a seed from "
                "memory_engine, so a dream does not reinvent an existing tool."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "seed": {"type": "string", "description": "Dream seed / topic"},
                    "k": {"type": "integer", "default": 5},
                },
                "required": ["seed"],
            },
        )
        self.tools["dreamz_gate"] = mt.Tool(
            name="dreamz_gate",
            title="Judge a Dream Candidate",
            description=(
                "Judge a dream candidate before promotion: epistemic veto "
                "(mem20crewz), AST lint (mem20verify), asset budget "
                "(mem20kilnz) and corpus distance (mem20corez). Returns a "
                "per-subsystem report and a promotable verdict."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "seed": {"type": "string", "description": "Dream seed"},
                    "candidate": {"type": "string", "description": "Candidate text"},
                    "triangles": {"type": "integer",
                                  "description": "Proposed triangle count, if any"},
                    "record": {"type": "boolean", "default": False,
                               "description": "Append the dream to the ledger"},
                },
                "required": ["seed", "candidate"],
            },
        )
        self.tools["dreamz_estate"] = mt.Tool(
            name="dreamz_estate",
            title="Estate Reality Check",
            description=(
                "Installed vs claimed vs phantom subsystems: what exists on disk "
                "versus what braid merely asserts."
            ),
            inputSchema={"type": "object", "properties": {}},
        )

    # ------------------------------------------------------------- handlers
    async def _dreamz_status(self, args: Dict[str, Any]) -> str:
        try:
            _ecosystem()
        except Exception as exc:  # noqa: BLE001
            return json.dumps({"ok": False, "available": False,
                               "error": f"{type(exc).__name__}: {exc}"}, indent=2)
        return json.dumps({
            "ok": True, "available": True,
            "subsystems": list(DREAMZ_SUBSYSTEMS),
            "gate": "DreamGate(ground -> judge)",
        }, indent=2)

    async def _dreamz_ground(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        return json.dumps(eco.ground_seed(args.get("seed", ""),
                                          k=int(args.get("k", 5))), indent=2)

    async def _dreamz_gate(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        out = eco.run_gate(
            seed=args.get("seed", ""),
            candidate=args.get("candidate", ""),
            triangles=args.get("triangles"),
            record=bool(args.get("record", False)),
        )
        return json.dumps(out, indent=2)

    async def _dreamz_estate(self, args: Dict[str, Any]) -> str:
        project = os.path.join(_REPO_ROOT, "mem20dreamz")
        if project not in sys.path:
            sys.path.insert(0, project)
        from mem20dreamz import estate  # type: ignore[import-not-found]

        return json.dumps(estate.estate_report(root=_REPO_ROOT), indent=2)
