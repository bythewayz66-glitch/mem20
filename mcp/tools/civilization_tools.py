"""Self-healing runtime civilization tools (RM-217).

Three MCP tools expose ``mem20selfhealingruntimecivilizationz``:

``civilization_health``
    Fleet status, per-agent health, repair budget and which mem20 substrate
    integrations resolved.
``civilization_cycle``
    Run one to five bounded self-healing cycles over the real catalogue.
``civilization_report``
    The full report: civilization state, planner actions, budget, metrics.

Every tool runs the real controller — ``gateway/gateway_civilization.py`` builds
(or reuses) a ``FleetController`` over the on-disk catalogue and calls it. Nothing
here fabricates a payload: if the subsystem cannot be imported, the tool raises
with the underlying reason instead of returning plausible-looking numbers.

Registration note: this module follows the same ``*ToolsMixin`` shape as
``braid_tools.py``. ``mcp/server.py`` composes its mixins from a hard-coded list,
so ``Mem20MCPServer`` must also inherit ``CivilizationToolsMixin`` for these tools
to be served; until that one-line change lands (it is queued as a follow-up in
``docs/renovation/4.0/FINDINGS.md``) the module is importable, tested, and the
tools are callable directly through ``CIVILIZATION_TOOLS``.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

try:  # the tools work without the SDK; only the mixin needs it
    import mcp_types as mt

    MCP_SDK_AVAILABLE = True
    MCP_SDK_IMPORT_ERROR = None
except ImportError as _mcp_sdk_exc:  # pragma: no cover - only without the SDK
    mt = None  # type: ignore[assignment]
    MCP_SDK_AVAILABLE = False
    MCP_SDK_IMPORT_ERROR = _mcp_sdk_exc

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_GATEWAY_DIR = os.path.join(_REPO_ROOT, "gateway")
if _GATEWAY_DIR not in sys.path:
    sys.path.insert(0, _GATEWAY_DIR)


def _controller(state_dir: str = None):
    """Build the controller through the gateway bridge (single code path).

    Imported lazily so importing this module never drags in the whole subsystem.
    """
    from gateway_civilization import controller_for

    return controller_for(state_dir)


# --- tool implementations ---------------------------------------------------

def civilization_health(state_dir: str = None) -> Dict[str, Any]:
    """Report the self-healing runtime civilization (RM-217)."""
    controller = _controller(state_dir)
    return {
        "roadmap": "RM-217",
        "subsystem": "mem20selfhealingruntimecivilizationz",
        "status": controller.civilization.status(),
        "health": controller.health(),
        "metrics": controller.metrics_snapshot(),
        "integrations": controller.integrations(),
    }


def civilization_cycle(cycles: int = 1, state_dir: str = None) -> Dict[str, Any]:
    """Run one to five bounded self-healing cycles over the real catalogue."""
    controller = _controller(state_dir)
    records = controller.run(cycles=max(1, min(5, int(cycles or 1))))
    return {
        "roadmap": "RM-217",
        "cycles": len(records),
        # the records are JSON-safe by construction (the controller stores them
        # through the same serialiser), so no ``default=str`` masking is needed
        "records": records,
    }


def civilization_report(state_dir: str = None) -> Dict[str, Any]:
    """Full RM-217 report: civilization state, planner actions, budget, metrics."""
    return _controller(state_dir).report()


#: Direct call table — what the tests and any non-MCP caller use.
CIVILIZATION_TOOLS = {
    "civilization_health": civilization_health,
    "civilization_cycle": civilization_cycle,
    "civilization_report": civilization_report,
}

_TOOL_SPEC = {
    "civilization_health": (
        "Self-healing runtime civilization (RM-217, mem20selfhealingruntimecivilizationz): "
        "fleet status, per-agent health, repair budget and resolved mem20 substrate integrations.",
        {
            "type": "object",
            "properties": {
                "state_dir": {
                    "type": "string",
                    "description": "Override the subsystem state directory",
                }
            },
            "required": [],
        },
    ),
    "civilization_cycle": (
        "Run bounded self-healing cycles (RM-217): quarantine unhealthy agents, cascade to "
        "their dependents, repair within the budget and persist each record."
    , {
        "type": "object",
        "properties": {
            "cycles": {"type": "integer", "default": 1, "minimum": 1, "maximum": 5},
            "state_dir": {
                "type": "string",
                "description": "Override the subsystem state directory",
            },
        },
        "required": [],
    }),
    "civilization_report": (
        "Full RM-217 report: civilization state, planner actions, kiln-derived repair "
        "budget and live metrics.",
        {
            "type": "object",
            "properties": {
                "state_dir": {
                    "type": "string",
                    "description": "Override the subsystem state directory",
                }
            },
            "required": [],
        },
    ),
}


def tool_specs() -> Dict[str, Dict[str, Any]]:
    """The MCP tool specs, independent of the SDK (used by the tests)."""
    return {
        name: {"description": desc, "inputSchema": schema}
        for name, (desc, schema) in _TOOL_SPEC.items()
    }


class CivilizationToolsMixin:
    """MCP mixin exposing the RM-217 civilization tools."""

    def register_civilization_tools(self):
        if not MCP_SDK_AVAILABLE:  # pragma: no cover - SDK present in CI
            raise RuntimeError(f"mcp SDK unavailable: {MCP_SDK_IMPORT_ERROR}")
        for name, (description, schema) in _TOOL_SPEC.items():
            self.tools[name] = mt.Tool(
                name=name,
                title=name.replace("_", " ").title(),
                description=description,
                inputSchema=schema,
            )

    async def _civilization_tool_result(self, name: str, arguments: Dict[str, Any]):
        """Dispatch one civilization tool and wrap the result for MCP."""
        fn = CIVILIZATION_TOOLS[name]
        result = fn(**arguments)
        return mt.TextContent(
            type="text", text=json.dumps(result, indent=2, sort_keys=True, default=str)
        )
