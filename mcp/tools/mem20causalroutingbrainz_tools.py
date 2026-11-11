"""mem20causalroutingbrainz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20causalroutingbrainz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20causalroutingbrainz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class CausalRoutingBrainToolsMixin:
    def register_causalroutingbrainz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["causalroutingbrainz_status"]=mt.Tool(name="causalroutingbrainz_status",title="Causal Routing Brain Status",description="Causal routing report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["causalroutingbrainz_doctor"]=mt.Tool(name="causalroutingbrainz_doctor",title="Causal Routing Brain Doctor",description="Probe 6 causal-routing peers.",inputSchema={"type":"object","properties":{}})
    async def _causalroutingbrainz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().routing_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _causalroutingbrainz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})

# --- compatibility re-exports ---
# The 2026-11-09 consolidation wave moved these classes into their own
# per-subsystem modules. mcp/server.py still imports them from here, so
# they are re-exported at module level to keep the server importable
# without dropping any mixin from Mem20MCPServer's bases.
from tools.mem20zerodowntimemigrationbrainz_tools import ZeroDowntimeMigrationBrainzToolsMixin
from tools.mem20skillbasedprogressionbrainz_tools import SkillBasedProgressionBrainToolsMixin
