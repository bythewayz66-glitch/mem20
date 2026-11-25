"""mem20personalautomationcanvasz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20personalautomationcanvasz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20personalautomationcanvasz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class PersonalAutomationCanvasToolsMixin:
    def register_personalautomationcanvasz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["personalautomationcanvasz_status"]=mt.Tool(name="personalautomationcanvasz_status",title="Personal Automation Canvas Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["personalautomationcanvasz_doctor"]=mt.Tool(name="personalautomationcanvasz_doctor",title="Personal Automation Canvas Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _personalautomationcanvasz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().canvas_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _personalautomationcanvasz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})
