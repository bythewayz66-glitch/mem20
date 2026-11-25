"""mem20simz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20simz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20simz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class ArchitectureSimulationSandboxzToolsMixin:
    def register_architecturesimulationsandboxz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["architecturesimulationsandboxz_status"]=mt.Tool(name="architecturesimulationsandboxz_status",title="Architecture Simulation Sandbox Status",description="Real status/health from mem20simz domain.",inputSchema={"type":"object","properties":{}})
    async def _architecturesimulationsandboxz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            topo={"nodes":[{"id":"n1","cpu":2}],"edges":[]}
            metrics=d.simulate_load(topo, rps=100, duration_s=10)
            rec=d.scaling_recommendation(metrics if isinstance(metrics,dict) else {"util":0.5}, target_util=0.7)
            cost=d.topology_cost(topo)
            return _d({"ok":True,"simulate_load":metrics,"scaling_recommendation":rec,"topology_cost":cost})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
