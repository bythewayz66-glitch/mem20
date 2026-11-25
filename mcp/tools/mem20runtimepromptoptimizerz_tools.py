"""mem20runtimepromptoptimizerz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20runtimepromptoptimizerz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20runtimepromptoptimizerz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class RuntimePromptOptimizerToolsMixin:
    def register_runtimepromptoptimizerz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["runtimepromptoptimizerz_status"]=mt.Tool(name="runtimepromptoptimizerz_status",title="Runtime Prompt Optimizer Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["runtimepromptoptimizerz_doctor"]=mt.Tool(name="runtimepromptoptimizerz_doctor",title="Runtime Prompt Optimizer Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _runtimepromptoptimizerz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().prompt_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _runtimepromptoptimizerz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})
