"""mem20dynamicphasereplannerz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20dynamicphasereplannerz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20dynamicphasereplannerz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class DynamicPhaseReplannerzToolsMixin:
    def register_dynamicphasereplannerz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["dynamicphasereplannerz_status"]=mt.Tool(name="dynamicphasereplannerz_status",title="Dynamic Phase Replanner Status",description="Real status/health from mem20dynamicphasereplannerz domain.",inputSchema={"type":"object","properties":{}})
    async def _dynamicphasereplannerz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            p=d.DynamicPhaseReplanner()
            p.phase("build", depends_on=["design"])
            p.phase("test", depends_on=["build"])
            p.phase("design", depends_on=[])
            order=p.order()
            return _d({"ok":True,"order":order})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
