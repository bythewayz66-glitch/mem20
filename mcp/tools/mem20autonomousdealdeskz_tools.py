"""mem20autonomousdealdeskz MCP tools — autonomous deal desk surface."""
from __future__ import annotations
import json, os, sys
from typing import Any, Dict
try:
    import mcp_types as mt
    MCP_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    MCP_SDK_AVAILABLE = False; mt = None  # type: ignore
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p = os.path.join(_REPO_ROOT, "mem20autonomousdealdeskz")
    if p not in sys.path: sys.path.insert(0, p)
    import mem20autonomousdealdeskz.domain as domain  # type: ignore
    return domain
def _dumps(v: Any) -> str: return json.dumps(v, indent=2, default=str)
class AutonomousDealDeskToolsMixin:
    def register_autonomousdealdeskz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["autonomousdealdeskz_status"] = mt.Tool(name="autonomousdealdeskz_status", title="Autonomous Deal Desk Status", description="Deal report with 6 subsystem-specific peer judgements.", inputSchema={"type":"object","properties":{}})
        self.tools["autonomousdealdeskz_doctor"] = mt.Tool(name="autonomousdealdeskz_doctor", title="Autonomous Deal Desk Doctor", description="Probe 6 deal-desk peers (economics, demand, partnership, guardrail, capability routing, sales pipeline).", inputSchema={"type":"object","properties":{}})
        self.tools["autonomousdealdeskz_price"] = mt.Tool(name="autonomousdealdeskz_price", title="Deal Desk Price", description="Price a deal.", inputSchema={"type":"object","properties":{"product":{"type":"object"},"customer":{"type":"object"}},"required":["product","customer"]})
    async def _autonomousdealdeskz_status(self, args: Dict[str, Any]) -> str:
        try: return _dumps(_load().deal_report())
        except Exception as e: return _dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
    async def _autonomousdealdeskz_doctor(self, args: Dict[str, Any]) -> str:
        try: return _dumps(_load().probe())
        except Exception as e: return _dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
    async def _autonomousdealdeskz_price(self, args: Dict[str, Any]) -> str:
        try: return _dumps({"price": _load().price_deal(args.get("product",{}), args.get("customer",{}))})
        except Exception as e: return _dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
