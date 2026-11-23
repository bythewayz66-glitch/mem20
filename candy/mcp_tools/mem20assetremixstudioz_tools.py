"""mem20studioz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20studioz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20studioz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AssetRemixStudiozToolsMixin:
    def register_assetremixstudioz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["assetremixstudioz_status"]=mt.Tool(name="assetremixstudioz_status",title="Asset Remix Studio Status",description="Real status/health from mem20studioz domain.",inputSchema={"type":"object","properties":{}})
    async def _assetremixstudioz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            asset={"id":"a1","type":"image","meta":{"w":100}}
            ops=[{"op":"resize","w":50}]
            r=d.remix([asset], ops)
            ex=d.export_formats(asset, ["png","webp"])
            return _d({"ok":True,"remix":r,"export_formats":ex})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
