"""mem20alternativedatabaseplaygroundz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20alternativedatabaseplaygroundz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20alternativedatabaseplaygroundz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class AlternativeDatabasePlaygroundzToolsMixin:
    def register_alternativedatabaseplaygroundz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["alternativedatabaseplaygroundz_status"]=mt.Tool(name="alternativedatabaseplaygroundz_status",title="Alternative Database Playground Status",description="Real status from mem20alternativedatabaseplaygroundz domain.",inputSchema={"type":"object","properties":{}})
    async def _alternativedatabaseplaygroundz_status(self,args:Dict[str,Any])->str:
        try:
            d=_load()
            plan=d.query_plan("SELECT * FROM t", ["t"])
            idx=d.suggest_index(["id","name"], [1000, 5])
            bench=d.benchmark_query(plan, rows=10000)
            cmp=d.compare_engines([{"engine":"pg","time_ms":10.0},{"engine":"sqlite","time_ms":4.0}])
            eff=d.index_efficiency(["id"], 2)
            return _d({"ok":True,"plan":plan,"suggest_index":idx,"benchmark_ms":bench,"compare_engines":cmp,"index_efficiency":eff})
        except Exception as e:
            return _d({"ok":False,"error":str(e)})
