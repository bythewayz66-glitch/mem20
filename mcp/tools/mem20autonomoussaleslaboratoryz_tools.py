"""mem20autonomoussaleslaboratoryz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20autonomoussaleslaboratoryz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20autonomoussaleslaboratoryz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AutonomousSalesLaboratoryToolsMixin:
    def register_autonomoussaleslaboratoryz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["autonomoussaleslaboratoryz_status"]=mt.Tool(name="autonomoussaleslaboratoryz_status",title="Sales Laboratory Status",description="Sales lab report with 6 peer judgements (anti-spam guarded).",inputSchema={"type":"object","properties":{}})
        self.tools["autonomoussaleslaboratoryz_doctor"]=mt.Tool(name="autonomoussaleslaboratoryz_doctor",title="Sales Laboratory Doctor",description="Probe 6 sales-lab peers.",inputSchema={"type":"object","properties":{}})
    async def _autonomoussaleslaboratoryz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().lab_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _autonomoussaleslaboratoryz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
