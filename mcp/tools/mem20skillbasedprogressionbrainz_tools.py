"""mem20skillbasedprogressionbrainz MCP tools."""
from __future__ import annotations
import json,os,sys
from typing import Any,Dict
try: import mcp_types as mt; MCP_SDK_AVAILABLE=True
except ImportError: MCP_SDK_AVAILABLE=False; mt=None  # type: ignore
_REPO_ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def _load():
    p=os.path.join(_REPO_ROOT,"mem20skillbasedprogressionbrainz")
    if p not in sys.path: sys.path.insert(0,p)
    import mem20skillbasedprogressionbrainz.domain as domain  # type: ignore
    return domain
def _d(v): return json.dumps(v,indent=2,default=str)
class SkillBasedProgressionBrainToolsMixin:
    def register_skillbasedprogressionbrainz_tools(self):
        if not MCP_SDK_AVAILABLE: return
        self.tools["skillbasedprogressionbrainz_status"]=mt.Tool(name="skillbasedprogressionbrainz_status",title="Skill-Based Progression Brain Status",description="Report with 6 peer judgements.",inputSchema={"type":"object","properties":{}})
        self.tools["skillbasedprogressionbrainz_doctor"]=mt.Tool(name="skillbasedprogressionbrainz_doctor",title="Skill-Based Progression Brain Doctor",description="Probe 6 peers.",inputSchema={"type":"object","properties":{}})
    async def _skillbasedprogressionbrainz_status(self,args:Dict[str,Any])->str:
        try: return _d(_load().progression_report())
        except Exception as e: return _d({"ok":False,"error":str(e)})
    async def _skillbasedprogressionbrainz_doctor(self,args:Dict[str,Any])->str:
        try: return _d(_load().probe())
        except Exception as e: return _d({"ok":False,"error":str(e)})
