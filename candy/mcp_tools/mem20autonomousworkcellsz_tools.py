"""mem20autonomousworkcellsz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20autonomousworkcellsz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20autonomousworkcellsz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AutonomousWorkcellsToolsMixin:
    def register_autonomousworkcellsz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["autonomousworkcellsz_status"]=mt.Tool(name="autonomousworkcellsz_status",title="Workcells Status",description="Workcell report with 6 workcell-specific peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["autonomousworkcellsz_doctor"]=mt.Tool(name="autonomousworkcellsz_doctor",title="Workcells Doctor",description="Probe 6 workcell peers.",inputSchema={"type":"object","properties":{}})
    async def _autonomousworkcellsz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().workcell_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _autonomousworkcellsz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
