"""mem20wasmz MCP tools — the WebAssembly component lab on the server surface.

The lab runs language-neutral components with explicit interfaces and strong
isolation. Two tools are exposed:

* ``wasmz_inspect`` — the roadmap identity and component surface
* ``wasmz_run``     — run one component request through the isolated runtime

Both go through the real ``Runtime``; neither fabricates a result. A run that
fails returns the real error text, and the audit block is produced by
``mem20wasmz.wiring.describe_run`` (six real cross-module calls).
"""
import json
import os
import sys
import tempfile
from typing import Any, Dict

try:
    from mcp.server import Server
    from mcp.server.lowlevel.server import ServerRequestContext
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
    MCP_SDK_IMPORT_ERROR = None
except ImportError as _mcp_sdk_exc:  # pragma: no cover - only without the SDK
    MCP_SDK_AVAILABLE = False
    MCP_SDK_IMPORT_ERROR = _mcp_sdk_exc

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_LAB_DIR = os.path.join(_REPO_ROOT, "mem20wasmz")
if _LAB_DIR not in sys.path:
    sys.path.insert(0, _LAB_DIR)


class WasmzToolsMixin:
    """MCP tools exposing the mem20wasmz component lab."""

    def register_wasmz_tools(self):
        self.tools["wasmz_inspect"] = mt.Tool(
            name="wasmz_inspect",
            title="Wasmz Inspect",
            description="Show the WebAssembly component lab roadmap identity and component surface.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        self.tools["wasmz_run"] = mt.Tool(
            name="wasmz_run",
            title="Wasmz Run",
            description=(
                "Run one component request through the isolated mem20wasmz runtime. "
                "Returns the real run result plus an audit block (canonical form, "
                "stable hash, and the state of the six wired mem20 subsystems)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "object",
                        "description": 'Component request, e.g. {"text": "demo", "cache": false}',
                    },
                },
                "required": ["request"],
            },
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    async def _wasmz_inspect(self, args: Dict) -> str:
        try:
            from mem20wasmz.cli import ROADMAP_PATH
            from mem20wasmz.core import load_roadmap

            roadmap = load_roadmap(ROADMAP_PATH)
            phases = roadmap.get("phases") or []
            return json.dumps(
                {
                    "global_id": roadmap.get("global_id"),
                    "title": roadmap.get("title"),
                    "owner": roadmap.get("owner"),
                    "lane": roadmap.get("lane"),
                    "outcome": roadmap.get("outcome"),
                    "phases": len(phases),
                    "subphases": sum(len(p.get("subphases") or []) for p in phases),
                },
                indent=2,
            )
        except Exception as e:
            return f"Error: {e}"

    async def _wasmz_run(self, args: Dict) -> str:
        request = args.get("request")
        if not isinstance(request, dict):
            return "Error: request must be an object"
        try:
            from mem20wasmz.cli import ROADMAP_PATH
            from mem20wasmz.core import Runtime, load_roadmap
            from mem20wasmz import wiring

            runtime = Runtime(
                load_roadmap(ROADMAP_PATH),
                data_dir=tempfile.mkdtemp(prefix="mem20wasmz-mcp-"),
            )
            result = runtime.run(request)
            return json.dumps(
                {"result": result, "audit": wiring.describe_run(result)},
                indent=2,
                default=str,
            )
        except Exception as e:
            return f"Error: {e}"


def install() -> bool:
    """Attach the mem20wasmz tools to the verify-tools mixin.

    ``mcp/server.py`` is an 80 KB module that is expensive and risky to transmit
    through the contents API, so the registration is attached here instead of
    editing the server -- the same pattern ``rm239_tools`` and ``rm052_tools``
    already use. ``Mem20MCPServer._setup_tools`` calls
    ``register_verify_tools()``, so wrapping that one method is enough for both
    tools to appear in ``self.tools`` and to be dispatched by the
    ``_<tool_name>`` convention in ``_execute_tool``.

    Idempotent: a second call is a no-op.
    """
    try:
        from tools.verify_tools import VerifyToolsMixin
    except Exception:
        try:
            from verify_tools import VerifyToolsMixin  # mcp/tools on sys.path
        except Exception:
            return False

    original = VerifyToolsMixin.register_verify_tools
    if getattr(original, "_wasmz_installed", False):
        return True

    def register_verify_tools(self):
        original(self)
        self.tools["wasmz_inspect"] = mt.Tool(
            name="wasmz_inspect",
            title="Wasmz Inspect",
            description="Show the WebAssembly component lab roadmap identity and component surface.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        self.tools["wasmz_run"] = mt.Tool(
            name="wasmz_run",
            title="Wasmz Run",
            description=(
                "Run one component request through the isolated mem20wasmz runtime. "
                "Returns the real run result plus an audit block (canonical form, "
                "stable hash, and the state of the six wired mem20 subsystems)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "object",
                        "description": 'Component request, e.g. {"text": "demo", "cache": false}',
                    },
                },
                "required": ["request"],
            },
        )
        # Bound as instance attributes: _execute_tool does
        # getattr(self, "_wasmz_inspect") and awaits it with (args). The
        # handlers are methods on WasmzToolsMixin, so bind them to this
        # instance rather than referencing a module-level name.
        self._wasmz_inspect = WasmzToolsMixin._wasmz_inspect.__get__(self, type(self))
        self._wasmz_run = WasmzToolsMixin._wasmz_run.__get__(self, type(self))

    register_verify_tools._wasmz_installed = True
    VerifyToolsMixin.register_verify_tools = register_verify_tools
    return True
