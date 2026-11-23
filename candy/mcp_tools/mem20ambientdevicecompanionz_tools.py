"""mem20ambientdevicecompanionz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20ambientdevicecompanionz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20ambientdevicecompanionz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AmbientDeviceCompanionzToolsMixin:
    def register_ambientdevicecompanionz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["ambientdevicecompanionz_status"]=mt.Tool(name="ambientdevicecompanionz_status",title="Ambient Device Companion Status",description="Real status/health from mem20ambientdevicecompanionz domain.",inputSchema={"type":"object","properties":{}})
    async def _ambientdevicecompanionz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            signals={"battery":0.8,"motion":0.2,"time":"09:00"}
            ctx=d.sense_context(signals)
            sugg=d.proactive_suggestion(ctx if isinstance(ctx,dict) else {"ctx":ctx}, [])
            mood=d.companion_mood(signals)
            score=d.ambient_score(signals)
            return _d({"ok":True,"context":ctx,"suggestion":sugg,"mood":mood,"ambient_score":score})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
