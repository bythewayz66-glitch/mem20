"""Mesh runtime tools \u2014 the six vendored mesh engines behind one door.

Thin by design. The engines, the admission policy and the provenance recording
all live in ``mem20meshz``; these tools are a door onto that runtime and nothing
more. Reimplementing the policy here would give an agent two sources of truth
about what a mesh may be used for, and the one that is not on the dispatch path
would be the one that is wrong.

The tool descriptions carry the two rules an agent needs: declare the intended
use, because the prohibited-use gate refuses an undeclared dangerous purpose
rather than guessing, and read ``mem20meshz_admission`` when a mesh result looks
suspiciously clean.
"""
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

MESH_NAMES = ("crisis", "crossdevice", "federated", "nearby", "offline", "selfhealing")


def _runtime():
    """Import the mesh runtime lazily.

    ``mem20meshz`` is a project directory in this estate, so importing it at
    module scope would make this tool module unimportable whenever the project
    root is not on sys.path \u2014 which is the normal case for the MCP server, whose
    cwd is ``mcp/``. Importing inside the handler keeps the tool registered and
    reports the real reason if the runtime is genuinely absent.
    """
    project = os.path.join(_REPO_ROOT, "mem20meshz")
    if project not in sys.path:
        sys.path.insert(0, project)
    from mem20meshz.runtime import MasterEngine

    return MasterEngine


class MeshToolsMixin:
    """MCP tools exposing the mem20meshz gold runtime."""

    def register_mesh_tools(self):
        self.tools["mem20meshz_list"] = mt.Tool(
            name="mem20meshz_list",
            title="Mesh List",
            description=(
                "List the six mesh engines the mem20meshz gold runtime "
                "orchestrates: crisis, crossdevice, federated, nearby, offline, "
                "selfhealing. Use this before dispatching to learn the valid "
                "mesh names."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        self.tools["mem20meshz_execute"] = mt.Tool(
            name="mem20meshz_execute",
            title="Mesh Execute",
            description=(
                "Dispatch a request to one mesh or all six, through admission "
                "control. Declare 'intended_uses' \u2014 the prohibited-use gate "
                "refuses a dangerous purpose rather than guessing at it. A "
                "refused mesh is reported in the result with the check that "
                "refused it; it is never silently skipped."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "object",
                        "description": "Domain payload for the mesh.",
                        "default": {},
                    },
                    "only": {
                        "type": "string",
                        "description": "Run just this mesh instead of all six.",
                        "enum": list(MESH_NAMES),
                    },
                    "intended_uses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "What this execution is for. Checked against the "
                            "estate's prohibited-use list before any mesh runs."
                        ),
                        "default": [],
                    },
                    "at": {
                        "type": "string",
                        "description": "ISO-8601 instant, checked against the mesh's operating window.",
                    },
                },
                "required": [],
            },
        )
        self.tools["mem20meshz_admission"] = mt.Tool(
            name="mem20meshz_admission",
            title="Mesh Admission Report",
            description=(
                "What admission control decided for the last execution of each "
                "mesh: tool naming, declared uses, wire lines kept vs swallowed, "
                "stub issues, and whether the instant was inside the operating "
                "window. Use this when a mesh result looks suspiciously clean."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        )
        self.tools["mem20meshz_provenance"] = mt.Tool(
            name="mem20meshz_provenance",
            title="Mesh Provenance Report",
            description=(
                "Where each mesh execution was recorded on the braid ledger, and "
                "whether it was actually committed. A node that was not committed "
                "reports the reason rather than being silently skipped."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    async def _mem20meshz_list(self, args: Dict) -> str:
        try:
            MasterEngine = _runtime()
            engine = MasterEngine()
            return json.dumps(sorted(engine.engines), indent=2)
        except Exception as e:
            return f"Error: {e}"

    async def _mem20meshz_execute(self, args: Dict) -> str:
        try:
            MasterEngine = _runtime()
            request = dict(args.get("request") or {})
            if args.get("intended_uses"):
                request["intended_uses"] = list(args["intended_uses"])
            if args.get("at"):
                request["at"] = args["at"]
            engine = MasterEngine()
            return json.dumps(
                engine.execute(request, args.get("only")), indent=2, default=str
            )
        except Exception as e:
            return f"Error: {e}"

    async def _mem20meshz_admission(self, args: Dict) -> str:
        try:
            MasterEngine = _runtime()
            return json.dumps(MasterEngine().admission_report(), indent=2, default=str)
        except Exception as e:
            return f"Error: {e}"

    async def _mem20meshz_provenance(self, args: Dict) -> str:
        try:
            MasterEngine = _runtime()
            return json.dumps(MasterEngine().provenance_report(), indent=2, default=str)
        except Exception as e:
            return f"Error: {e}"
