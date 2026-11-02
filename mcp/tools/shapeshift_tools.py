"""API shape-shifting gateway tools - translate a payload between API shapes.

Thin by design: the gateway's own runtime does the work, and this module only
exposes it to the MCP surface. Every call goes through the gateway's admission
control, so a prohibited purpose, a non-address route, a stubbed transform, a
retired API version or a lossy mapping is refused here exactly as it is in the
CLI. Nothing is re-implemented and nothing is bypassed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATEWAY = _REPO_ROOT / "mem20apishapeshiftinggatewayz"
if str(_GATEWAY) not in sys.path:
    sys.path.insert(0, str(_GATEWAY))

from mem20apishapeshiftinggatewayz import governance  # noqa: E402
from mem20apishapeshiftinggatewayz.runtime import Engine, load_config  # noqa: E402

try:
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - only without the SDK
    MCP_SDK_AVAILABLE = False

_ENGINE = None


def _engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine(load_config(str(_GATEWAY / "CAPABILITY.json")))
    return _ENGINE


def _refusal(exc: governance.GatewayRefused) -> dict:
    return exc.as_dict()


def gateway_translate(
    goal: str,
    candidates: list | None = None,
    route: str | None = None,
    version: str | None = None,
    intended_uses: list | None = None,
    mapping: dict | None = None,
    wire: list | None = None,
    at: str | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> dict:
    """Translate a payload between API shapes, through admission control.

    Args:
        goal: what the translation is for
        candidates: candidate shapes to consider
        route: the gateway route; must be an estate address
        version: the API version being targeted
        intended_uses: declared purpose; checked against the prohibited-use list
        mapping: field renames to apply; a mapping that loses a field is refused
        wire: upstream lines to filter before they become a request
        at: ISO-8601 instant to check against the version window
        valid_from: start of the version window
        valid_to: end of the version window

    Returns:
        The translation result, or a structured refusal.
    """
    payload = {"goal": goal}
    if candidates is not None:
        payload["candidates"] = candidates
    for key, value in (
        ("route", route), ("version", version), ("intended_uses", intended_uses),
        ("mapping", mapping), ("wire", wire), ("at", at),
        ("valid_from", valid_from), ("valid_to", valid_to),
    ):
        if value is not None:
            payload[key] = value
    try:
        return _engine().execute(payload)
    except governance.GatewayRefused as exc:
        return _refusal(exc)


def gateway_admission() -> dict:
    """What admission control decided for the last translation of each route."""
    return _engine().admission_report()


def gateway_provenance() -> dict:
    """Where each translation was recorded, and whether braid committed it."""
    return _engine().provenance_report()


GATEWAY_TOOLS = {
    "gateway_translate": {
        "function": gateway_translate,
        "description": (
            "Translate a payload between incompatible API shapes. Goes through "
            "admission control: a prohibited purpose, a non-address route, a "
            "stubbed transform, a retired version or a lossy field mapping is "
            "refused rather than applied."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "What the translation is for"},
                "candidates": {"type": "array", "items": {"type": "object"},
                               "description": "Candidate shapes to consider"},
                "route": {"type": "string", "description": "Gateway route; must be an estate address"},
                "version": {"type": "string", "description": "Target API version"},
                "intended_uses": {"type": "array", "items": {"type": "string"},
                                  "description": "Declared purpose; checked against the prohibited-use list"},
                "mapping": {"type": "object", "description": "Field renames; a lossy mapping is refused"},
                "wire": {"type": "array", "items": {"type": "object"},
                         "description": "Upstream lines to filter"},
                "at": {"type": "string", "description": "ISO-8601 instant for the version window"},
                "valid_from": {"type": "string"},
                "valid_to": {"type": "string"},
            },
            "required": ["goal"],
        },
    },
    "gateway_admission": {
        "function": gateway_admission,
        "description": "What admission control decided for the last translation of each route",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "gateway_provenance": {
        "function": gateway_provenance,
        "description": "Where each translation was recorded, and whether braid committed it",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


def get_gateway_tools() -> dict:
    """Return the tool catalog for MCP server registration."""
    return GATEWAY_TOOLS


class ShapeShiftToolsMixin:
    """MCP surface for the API shape-shifting gateway.

    Registered on the canonical server so the gateway is reachable from any MCP
    host. Every call goes through the gateway's admission control -- this mixin
    adds no path that bypasses it.
    """

    def register_shapeshift_tools(self):
        if not MCP_SDK_AVAILABLE:
            return
        self.tools["gateway_translate"] = mt.Tool(
            name="gateway_translate",
            title="Translate Between API Shapes",
            description=(
                "Translate a payload between incompatible API shapes. Goes "
                "through admission control: a prohibited purpose, a non-address "
                "route, a stubbed transform, a retired version or a lossy field "
                "mapping is refused rather than applied."
            ),
            inputSchema=GATEWAY_TOOLS["gateway_translate"]["parameters"],
        )
        self.tools["gateway_admission"] = mt.Tool(
            name="gateway_admission",
            title="Gateway Admission Report",
            description="What admission control decided for the last translation of each route",
            inputSchema={"type": "object", "properties": {}},
        )
        self.tools["gateway_provenance"] = mt.Tool(
            name="gateway_provenance",
            title="Gateway Provenance Report",
            description="Where each translation was recorded, and whether braid committed it",
            inputSchema={"type": "object", "properties": {}},
        )

    async def _gateway_translate(self, args: dict) -> str:
        return json.dumps(gateway_translate(**args), indent=2, default=str)

    async def _gateway_admission(self, args: dict) -> str:
        return json.dumps(gateway_admission(), indent=2, default=str)

    async def _gateway_provenance(self, args: dict) -> str:
        return json.dumps(gateway_provenance(), indent=2, default=str)


def call_gateway_tool(tool_name: str, arguments: dict) -> dict:
    """Dispatch a gateway tool call. This is the entry point for the MCP server."""
    if tool_name not in GATEWAY_TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    func = GATEWAY_TOOLS[tool_name]["function"]
    try:
        return {"result": func(**arguments)}
    except Exception as exc:
        return {"error": f"Tool execution failed: {exc}"}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="API shape-shifting gateway tools")
    parser.add_argument("tool")
    parser.add_argument("--json-args", "-j", default="{}")
    args = parser.parse_args()
    print(json.dumps(call_gateway_tool(args.tool, json.loads(args.json_args)),
                     indent=2, default=str))
