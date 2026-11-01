"""mem20agentz MCP tools — the agent platform's grounded turn surface.

Exposes the agent platform to any MCP host. Every tool here routes through
``mem20agentz.ecosystem``, so a call from a client exercises the same
cross-subsystem wiring the tests do: grounded recall from ``memory_engine``,
the epistemic veto from ``mem20crewz``, fidelity from ``mem20dreamz``, AST
checks from ``mem20verify``, asset budgets from ``mem20kilnz`` and the
char-MLP perplexity from ``mem20corez``.

Tools:

- ``agentz_status``      — is the platform importable, and what does it wire to
- ``agentz_ground``      — grounded context for a topic (memory_engine)
- ``agentz_review``      — review an answer against a brief (all six subsystems)
- ``agentz_run``         — one conversational turn through AgentCore

The import is lazy and guarded: a host that has not installed the platform
still gets ``agentz_status`` reporting the absence, rather than a server that
fails to start.
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

#: The subsystems this surface depends on, in the order a turn uses them.
AGENTZ_SUBSYSTEMS = (
    "memory_engine", "mem20crewz", "mem20dreamz",
    "mem20verify", "mem20kilnz", "mem20corez", "mem20cliz",
)


def _ecosystem():
    """Import mem20agentz.ecosystem, preferring the project directory.

    The estate layout is ``<repo>/mem20agentz/mem20agentz/``, so the repo root
    alone resolves the *outer* directory as a namespace package. Put the
    project directory first so the real package wins.
    """
    project = os.path.join(_REPO_ROOT, "mem20agentz")
    if project not in sys.path:
        sys.path.insert(0, project)
    from mem20agentz import ecosystem  # type: ignore[import-not-found]
    return ecosystem


class AgentzToolsMixin:
    """mem20agentz tools for the mem20 MCP server."""

    def register_agentz_tools(self):
        self.tools["agentz_status"] = mt.Tool(
            name="agentz_status",
            title="Agent Platform Status",
            description=(
                "Report whether the mem20agentz agent platform is importable and "
                "which mem20 subsystems its grounded-turn pipeline wires to."
            ),
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["agentz_ground"] = mt.Tool(
            name="agentz_ground",
            title="Ground a Prompt",
            description=(
                "Read grounded facts for a topic from memory_engine before an "
                "agent reasons. Simulated content is excluded by the engine."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Memory topic"},
                    "k": {"type": "integer", "default": 5,
                          "description": "Max facts to return"},
                },
                "required": ["topic"],
            },
        )
        self.tools["agentz_review"] = mt.Tool(
            name="agentz_review",
            title="Review an Answer",
            description=(
                "Review an answer against its brief using the wider estate: "
                "epistemic veto (mem20crewz), fidelity/divergence (mem20dreamz), "
                "AST lint (mem20verify), asset budget (mem20kilnz) and char-MLP "
                "perplexity (mem20corez). Returns a per-subsystem report."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The brief"},
                    "answer": {"type": "string", "description": "The answer to review"},
                    "topic": {"type": "string", "description": "Memory topic to ground against"},
                    "record": {"type": "boolean", "default": False,
                               "description": "Append the turn to the grounded ledger"},
                },
                "required": ["prompt", "answer"],
            },
        )
        self.tools["agentz_run"] = mt.Tool(
            name="agentz_run",
            title="Run an Agent Turn",
            description=(
                "Run one conversational turn through the mem20agentz AgentCore "
                "loop, then review the result with the estate's verifiers."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "User prompt"},
                    "profile": {"type": "string", "default": "mem20"},
                    "max_iter": {"type": "integer", "default": 4},
                },
                "required": ["prompt"],
            },
        )

    # ------------------------------------------------------------- handlers
    async def _agentz_status(self, args: Dict[str, Any]) -> str:
        try:
            eco = _ecosystem()
        except Exception as exc:  # noqa: BLE001
            return json.dumps({
                "ok": False,
                "available": False,
                "error": f"{type(exc).__name__}: {exc}",
            }, indent=2)
        return json.dumps({
            "ok": True,
            "available": True,
            "subsystems": list(AGENTZ_SUBSYSTEMS),
            "pipeline": "GroundingPipeline(prepare -> review)",
        }, indent=2)

    async def _agentz_ground(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        out = eco.grounded_context(topic=args.get("topic"),
                                   k=int(args.get("k", 5)))
        return json.dumps(out, indent=2)

    async def _agentz_review(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        out = eco.run_pipeline(
            prompt=args.get("prompt", ""),
            answer=args.get("answer", ""),
            topic=args.get("topic"),
            record=bool(args.get("record", False)),
        )
        return json.dumps(out, indent=2)

    async def _agentz_run(self, args: Dict[str, Any]) -> str:
        eco = _ecosystem()
        project = os.path.join(_REPO_ROOT, "mem20agentz")
        if project not in sys.path:
            sys.path.insert(0, project)
        from mem20agentz.agentz import AgentCore  # type: ignore[import-not-found]

        core = AgentCore(profile=args.get("profile", "mem20"),
                         max_iter=int(args.get("max_iter", 4)))
        result = core.run(args.get("prompt", ""))
        review = eco.run_pipeline(prompt=args.get("prompt", ""),
                                  answer=result.text)
        return json.dumps({
            "ok": True,
            "text": result.text,
            "blocked": result.blocked,
            "reason": result.reason,
            "steps": [{"index": s.index, "action": s.action,
                       "tool": s.tool, "output": s.output[:400]}
                      for s in result.steps],
            "review": review,
        }, indent=2)
