"""mem20asynccollaborationcapsulesz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20asynccollaborationcapsulesz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20asynccollaborationcapsulesz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AsyncCollaborationCapsuleszToolsMixin:
    def register_asynccollaborationcapsulesz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["asynccollaborationcapsulesz_status"]=mt.Tool(name="asynccollaborationcapsulesz_status",title="Async Collaboration Capsules Status",description="Real status/health from mem20asynccollaborationcapsulesz domain.",inputSchema={"type":"object","properties":{}})
    async def _asynccollaborationcapsulesz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            cap=d.create_capsule("c1", members=["u1"])
            applied=d.apply_change(cap,"u1",{"path":"x","value":1})
            chk=d.capsule_checksum(cap)
            active=d.active_members(cap)
            return _d({"ok":True,"capsule":cap.get("name") if isinstance(cap,dict) else str(cap),"applied":applied,"checksum":chk,"active_members":active})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
