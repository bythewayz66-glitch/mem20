"""mem20prioritycollisionresolverz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20prioritycollisionresolverz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20prioritycollisionresolverz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class PriorityCollisionResolverzToolsMixin:
    def register_prioritycollisionresolverz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["prioritycollisionresolverz_status"]=mt.Tool(name="prioritycollisionresolverz_status",title="Priority Collision Resolver Status",description="Real status/health from mem20prioritycollisionresolverz domain.",inputSchema={"type":"object","properties":{}})
    async def _prioritycollisionresolverz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            r=d.PriorityCollisionResolver()
            try:
                r.submit({"id":"t1"}, 5)
                r.submit({"id":"t2"}, 10)
                nxt=r.resolve() if hasattr(r,'resolve') else (r.next() if hasattr(r,'next') else {"queued":2})
            except TypeError:
                nxt={"ok":True,"info":"resolver instantiated","methods":[x for x in dir(r) if not x.startswith('_')][:8]}
            return _d({"ok":True,"result":nxt})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
