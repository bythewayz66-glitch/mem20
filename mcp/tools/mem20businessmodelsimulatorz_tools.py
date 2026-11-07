"""mem20businessmodelsimulatorz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20businessmodelsimulatorz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20businessmodelsimulatorz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class BusinessModelSimulatorToolsMixin:
    def register_businessmodelsimulatorz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["businessmodelsimulatorz_status"]=mt.Tool(name="businessmodelsimulatorz_status",title="Business Model Simulator Status",description="Business model report with 6 estate peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["businessmodelsimulatorz_doctor"]=mt.Tool(name="businessmodelsimulatorz_doctor",title="Business Model Simulator Doctor",description="Probe 6 business-model peers.",inputSchema={"type":"object","properties":{}})
    async def _businessmodelsimulatorz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().model_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _businessmodelsimulatorz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
