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
class SimzToolsMixin:
    def register_simz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["simz_status"]=mt.Tool(name="simz_status",title="Simz Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["simz_doctor"]=mt.Tool(name="simz_doctor",title="Simz Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _simz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().sim_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _simz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})

# --- compatibility re-exports ---
# The 2026-11-09 consolidation wave moved these classes into their own
# per-subsystem modules. mcp/server.py still imports them from here, so
# they are re-exported at module level to keep the server importable
# without dropping any mixin from Mem20MCPServer's bases.
from tools.mem20architecturesimulationsandboxz_tools import ArchitectureSimulationSandboxzToolsMixin
from tools.mem20outcomesimulationlabz_tools import OutcomeSimulationLabToolsMixin
from tools.mem20productledgrowthsimulatorz_tools import ProductLedGrowthSimulatorToolsMixin
from tools.mem20businessmodelsimulatorz_tools import BusinessModelSimulatorToolsMixin
from tools.mem20counterfactualmemorysimulatorz_tools import CounterfactualMemorySimulatorToolsMixin
