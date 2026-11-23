"""mem20zerotouchnodeswarmz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20zerotouchnodeswarmz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20zerotouchnodeswarmz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class ZeroTouchNodeSwarmToolsMixin:
    def register_zerotouchnodeswarmz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["zerotouchnodeswarmz_status"]=mt.Tool(name="zerotouchnodeswarmz_status",title="Zero-Touch Node Swarm Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["zerotouchnodeswarmz_doctor"]=mt.Tool(name="zerotouchnodeswarmz_doctor",title="Zero-Touch Node Swarm Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _zerotouchnodeswarmz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().swarm_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _zerotouchnodeswarmz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})
