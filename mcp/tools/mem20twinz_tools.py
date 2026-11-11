"""mem20twinz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20twinz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20twinz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class TwinzToolsMixin:
    def register_twinz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["twinz_status"]=mt.Tool(name="twinz_status",title="Twinz Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["twinz_doctor"]=mt.Tool(name="twinz_doctor",title="Twinz Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _twinz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().twin_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _twinz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})

# --- compatibility re-exports ---
# The 2026-11-09 consolidation wave moved these classes into their own
# per-subsystem modules. mcp/server.py still imports them from here, so
# they are re-exported at module level to keep the server importable
# without dropping any mixin from Mem20MCPServer's bases.
from tools.mem20personalworkflowtwinz_tools import PersonalWorkflowTwinToolsMixin
from tools.mem20realtimebusinesstwinz_tools import RealTimeBusinessTwinToolsMixin
from tools.mem20playermotivationtwinz_tools import PlayerMotivationTwinToolsMixin
from tools.mem20customerdigitaltwinlabz_tools import CustomerDigitalTwinLabToolsMixin
