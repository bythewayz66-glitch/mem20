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
class ZeroDowntimeMigrationBrainzToolsMixin:
    def register_zerodowntimemigrationbrainz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["zerodowntimemigrationbrainz_status"]=mt.Tool(name="zerodowntimemigrationbrainz_status",title="Zero-Downtime Migration Brain Status",description="Real status/health from mem20causalroutingbrainz domain.",inputSchema={"type":"object","properties":{}})
    async def _zerodowntimemigrationbrainz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            b=d.ZeroDowntimeMigrationBrain()
            info={"ok":True,"info":"migration brain instantiated","methods":[x for x in dir(b) if not x.startswith('_')][:10]}
            if hasattr(b,'plan'):
                try: info["plan"]=b.plan(source="a", target="b")
                except Exception: pass
            return _d(info)
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
