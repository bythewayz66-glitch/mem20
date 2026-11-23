"""mem20spatialcommanduniversez MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20spatialcommanduniversez")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20spatialcommanduniversez.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class SpatialCommandUniverseToolsMixin:
    def register_spatialcommanduniversez_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["spatialcommanduniversez_status"]=mt.Tool(name="spatialcommanduniversez_status",title="Spatial Command Universe Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["spatialcommanduniversez_doctor"]=mt.Tool(name="spatialcommanduniversez_doctor",title="Spatial Command Universe Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _spatialcommanduniversez_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().spatial_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _spatialcommanduniversez_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})
