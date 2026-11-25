"""mem20autonomousrecoverydirectorz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try:
    import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20autonomousrecoverydirectorz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20autonomousrecoverydirectorz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AutonomousRecoveryDirectorToolsMixin:
    def register_autonomousrecoverydirectorz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["autonomousrecoverydirectorz_status"]=mt.Tool(name="autonomousrecoverydirectorz_status",title="Recovery Director Status",description="Recovery report with 6 recovery-specific peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["autonomousrecoverydirectorz_doctor"]=mt.Tool(name="autonomousrecoverydirectorz_doctor",title="Recovery Director Doctor",description="Probe 6 recovery peers.",inputSchema={"type":"object","properties":{}})
    async def _autonomousrecoverydirectorz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().recovery_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _autonomousrecoverydirectorz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
