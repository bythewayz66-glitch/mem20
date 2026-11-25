"""mem20ambientteamradioz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20ambientteamradioz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20ambientteamradioz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AmbientTeamRadiozToolsMixin:
    def register_ambientteamradioz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["ambientteamradioz_status"]=mt.Tool(name="ambientteamradioz_status",title="Ambient Team Radio Status",description="Real status/health from mem20ambientteamradioz domain.",inputSchema={"type":"object","properties":{}})
    async def _ambientteamradioz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            ch=d.create_channel("ops", members=["a","b"])
            d.join_channel(ch,"c")
            msg=d.send_message(ch,"a","hello")
            act=d.channel_activity(ch)
            return _d({"ok":True,"channel":ch.get("name") if isinstance(ch,dict) else str(ch),"message":msg,"activity":act})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
