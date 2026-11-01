"""RM-052 reversible execution graph tools for the mem20 MCP server.

Registers ``graph_execute_reversible_plan``, which delegates to
``mem20reversibleexecutiongraphz.integration.execute_reversible_plan``.
"""

import json
import sys
from pathlib import Path
from typing import Dict

try:
    from mcp.server import Server
    from mcp.server.lowlevel.server import ServerRequestContext
    import mcp_types as mt
except ImportError:
    print("Error: mcp package not installed. Please install with: pip install mcp")
    raise

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RM052_DIR = _REPO_ROOT / "mem20reversibleexecutiongraphz"
if str(_RM052_DIR) not in sys.path:
    sys.path.insert(0, str(_RM052_DIR))

try:
    from mem20reversibleexecutiongraphz import domain as rm052_domain
    from mem20reversibleexecutiongraphz.integration import (
        execute_reversible_plan as rm052_execute_plan,
        rollback_plan as rm052_rollback_plan,
    )
    RM052_AVAILABLE = True
except Exception:  # optional deps of the integration layer may be absent
    rm052_domain = None
    rm052_execute_plan = None
    rm052_rollback_plan = None
    RM052_AVAILABLE = False


def _tool_spec():
    return mt.Tool(
        name="graph_execute_reversible_plan",
        title="Execute Reversible Plan",
        description=(
            "Execute a multi-step plan onto a reversible execution graph: each "
            "step is credential-screened, budget-checked, recorded on the graph "
            "and written to the grounded ledger, and the run reports whether it "
            "can be fully undone. Backed by mem20reversibleexecutiongraphz (RM-052)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "payload": {"type": "object"},
                            "triangles": {"type": "integer"},
                        },
                        "required": ["id"],
                    },
                },
                "family": {"type": "string", "default": "prop"},
            },
            "required": ["plan_id", "steps"],
        },
    )


async def _handle(args: Dict) -> str:
    if not RM052_AVAILABLE:
        return "Error: mem20reversibleexecutiongraphz is not importable"
    try:
        result = rm052_execute_plan(
            plan_id=args.get("plan_id", ""),
            steps=args.get("steps") or [],
            family=args.get("family", "prop"),
        )
        return json.dumps(result, indent=2, sort_keys=True)
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def install() -> bool:
    """Attach the RM-052 tool to the version-control mixin.

    ``mcp/server.py`` is a 47 KB module that is expensive and risky to transmit
    through the contents API, so the registration is attached here instead of
    editing the server. ``Mem20MCPServer._setup_tools`` already calls
    ``register_versioncontrol_tools()``, so wrapping that one method is enough
    for the tool to appear in ``self.tools`` and to be dispatched by the
    ``_<tool_name>`` convention in ``_execute_tool``.

    Idempotent: a second call is a no-op.
    """
    try:
        from tools.versioncontrol_tools import VersionControlToolsMixin
    except Exception:
        return False

    original = VersionControlToolsMixin.register_versioncontrol_tools
    if getattr(original, "_rm052_installed", False):
        return True

    def register_versioncontrol_tools(self):
        original(self)
        self.tools["graph_execute_reversible_plan"] = _tool_spec()
        self._graph_execute_reversible_plan = _handle

    register_versioncontrol_tools._rm052_installed = True
    VersionControlToolsMixin.register_versioncontrol_tools = register_versioncontrol_tools
    return True
