"""mem20assistz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    if _REPO_ROOT not in sys.path: sys.path.insert(0,_REPO_ROOT)
    import mem20assistz.domain as domain  # type: ignore
    return domain
def _load_eco():
    if _REPO_ROOT not in sys.path: sys.path.insert(0,_REPO_ROOT)
    import mem20assistz.ecosystem as ecosystem  # type: ignore
    return ecosystem
def _d(v): return json.dumps(v,indent=2,default=str)
class AssistzToolsMixin:
    def register_assistz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["mem20assistz_status"]=mt.Tool(name="mem20assistz_status",title="Assistz Status",description="Report the assistz integration context across the estate.",inputSchema={"type":"object","properties":{}})
        self.tools["mem20assistz_doctor"]=mt.Tool(name="mem20assistz_doctor",title="Assistz Doctor",description="Probe the assistz peer subsystems.",inputSchema={"type":"object","properties":{}})
    async def _mem20assistz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().estate_context())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _mem20assistz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load_eco().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})
