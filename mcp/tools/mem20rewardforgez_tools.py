"""mem20rewardforgez MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20rewardforgez")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20rewardforgez.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class RewardForgeToolsMixin:
    def register_rewardforgez_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["rewardforgez_status"]=mt.Tool(name="rewardforgez_status",title="Reward Forge Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["rewardforgez_doctor"]=mt.Tool(name="rewardforgez_doctor",title="Reward Forge Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _rewardforgez_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().forge_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _rewardforgez_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})

# --- compatibility re-exports ---
# The 2026-11-09 consolidation wave moved these classes into their own
# per-subsystem modules. mcp/server.py still imports them from here, so
# they are re-exported at module level to keep the server importable
# without dropping any mixin from Mem20MCPServer's bases.
from tools.mem20specialistmodelforgez_tools import SpecialistModelForgeToolsMixin
from tools.mem20contextcompressionforgez_tools import ContextCompressionForgeToolsMixin
