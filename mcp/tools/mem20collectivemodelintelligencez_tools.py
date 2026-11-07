"""mem20collectivemodelintelligencez MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20collectivemodelintelligencez")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20collectivemodelintelligencez.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class CollectiveModelIntelligenceToolsMixin:
    def register_collectivemodelintelligencez_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["collectivemodelintelligencez_status"]=mt.Tool(name="collectivemodelintelligencez_status",title="Collective Model Intelligence Status",description="Collective model report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["collectivemodelintelligencez_doctor"]=mt.Tool(name="collectivemodelintelligencez_doctor",title="Collective Model Intelligence Doctor",description="Probe 6 collective-model peers.",inputSchema={"type":"object","properties":{}})
    async def _collectivemodelintelligencez_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().collective_report())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
    async def _collectivemodelintelligencez_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":f"{type(e).__name__}: {e}"})
