"""RM-239 large-asset release audit tools for the mem20 MCP server.

Registers ``vcs_asset_release_audit``, which delegates to
``mem20versioncontrollargeassetandrecoverypipelinez.integration.audit_asset_release``.
Keeping the registration in its own mixin means the subsystem is wired into the
MCP surface without editing the large version-control mixin.
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
_RM239_DIR = _REPO_ROOT / "mem20versioncontrollargeassetandrecoverypipelinez"
if str(_RM239_DIR) not in sys.path:
    sys.path.insert(0, str(_RM239_DIR))

try:
    from mem20versioncontrollargeassetandrecoverypipelinez import domain as rm239_domain
    from mem20versioncontrollargeassetandrecoverypipelinez.integration import (
        audit_asset_release as rm239_audit_asset_release,
    )
    RM239_AVAILABLE = True
except Exception:  # optional deps of the integration layer may be absent
    rm239_domain = None
    rm239_audit_asset_release = None
    RM239_AVAILABLE = False


class RM239ToolsMixin:
    """Large-asset versioning + recovery pipeline (RM-239)."""

    def register_rm239_tools(self):
        self.tools["vcs_asset_release_audit"] = mt.Tool(
            name="vcs_asset_release_audit",
            title="Large-Asset Release Audit",
            description=(
                "Version a large asset (scene/model/media) and audit the release: "
                "credential screening, asset budget, grounded ledger write + "
                "read-back, store integrity, and estate registration. "
                "Backed by mem20versioncontrollargeassetandrecoverypipelinez (RM-239)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "asset_id": {"type": "string"},
                    "content": {"type": "string", "default": ""},
                    "family": {"type": "string", "default": "prop"},
                    "triangles": {"type": "integer", "default": 0},
                    "metadata": {"type": "object", "default": {}},
                },
                "required": ["asset_id"],
            },
        )

    async def _vcs_asset_release_audit(self, args: Dict) -> str:
        if not RM239_AVAILABLE:
            return "Error: mem20versioncontrollargeassetandrecoverypipelinez is not importable"
        try:
            result = rm239_audit_asset_release(
                asset_id=args.get("asset_id", ""),
                content=args.get("content", ""),
                family=args.get("family", "prop"),
                triangles=int(args.get("triangles", 0) or 0),
                metadata=args.get("metadata") or {},
            )
            return json.dumps(result, indent=2, sort_keys=True)
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"
