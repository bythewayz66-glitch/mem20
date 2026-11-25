"""mem20autonomousmicrosaasfoundryz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try:
    import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20autonomousmicrosaasfoundryz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20autonomousmicrosaasfoundryz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AutonomousMicroSaaSFoundryToolsMixin:
    def register_autonomousmicrosaasfoundryz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["autonomousmicrosaasfoundryz_status"]=mt.Tool(name="autonomousmicrosaasfoundryz_status",title="Micro-SaaS Foundry Status",description="Foundry report with 6 subsystem-specific peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["autonomousmicrosaasfoundryz_doctor"]=mt.Tool(name="autonomousmicrosaasfoundryz_doctor",title="Micro-SaaS Foundry Doctor",description="Probe 6 foundry peers.",inputSchema={"type":"object","properties":{}})
    async def _autonomousmicrosaasfoundryz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().foundry_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _autonomousmicrosaasfoundryz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
