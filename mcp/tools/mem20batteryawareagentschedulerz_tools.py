"""mem20batteryawareagentschedulerz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20batteryawareagentschedulerz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20batteryawareagentschedulerz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class BatteryAwareAgentSchedulerzToolsMixin:
    def register_batteryawareagentschedulerz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["batteryawareagentschedulerz_status"]=mt.Tool(name="batteryawareagentschedulerz_status",title="Battery-Aware Agent Scheduler Status",description="Real status/health from mem20batteryawareagentschedulerz domain.",inputSchema={"type":"object","properties":{}})
    async def _batteryawareagentschedulerz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            s=d.BatteryAwareAgentScheduler(power_budget_watts=100, rates={9:1.0,10:2.0,11:1.5})
            slot=s.cheapest_slot(work_units=10, hours=[9,10,11])
            plan=s.schedule(work_units=10, hours=[9,10,11])
            return _d({"ok":True,"cheapest_slot":slot,"schedule":plan,"budget":s.budget})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
