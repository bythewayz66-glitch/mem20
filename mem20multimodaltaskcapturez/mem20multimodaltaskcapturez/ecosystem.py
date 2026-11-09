"""6 unique peers for Multimodal Task Capture (#338)."""
from __future__ import annotations
from typing import Any, Callable, Dict, Mapping
def _safe(name:str,fn:Callable[[],Dict[str,Any]])->Dict[str,Any]:
 try:
  res=fn(); out={"ok":True,"subsystem":name}
  if isinstance(res,dict): out.update(res)
  else: out["result"]=res
  return out
 except Exception as e: return {"ok":False,"subsystem":name,"error":f"{type(e).__name__}: {e}"}

def modality_bridge_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20modalitybridgez.domain import analyze_bridge
  except Exception: from mem20modalitybridgez.mem20modalitybridgez.domain import analyze_bridge
  r=analyze_bridge({"from":ctx.get("modality","text"),"to":"text","payload":ctx.get("text","probe")})
  return {"analysis":r}
 return _safe("mem20modalitybridgez", run)

def sensory_ingest_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20sensorymemoryingestz.domain import ingest, recent
  except Exception: from mem20sensorymemoryingestz.mem20sensorymemoryingestz.domain import ingest, recent
  s={"events":[]}; ingest(s,{"text":ctx.get("text","task")},modality=ctx.get("modality","text")); rec=recent(s,1)
  return {"recent":rec}
 return _safe("mem20sensorymemoryingestz", run)

def intent_compile_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20intentcompilerz.domain import parse_intent, compile_to_action
  except Exception: from mem20intentcompilerz.mem20intentcompilerz.domain import parse_intent, compile_to_action
  i=parse_intent(str(ctx.get("text") or "create task")); a=compile_to_action(i)
  return {"intent":i,"action":a}
 return _safe("mem20intentcompilerz", run)

def task_capture_personal_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20twinz.domain import create_twin, observe, twin_health
  except Exception: from mem20twinz.mem20twinz.domain import create_twin, observe, twin_health
  twin=create_twin({"user":"probe"}); observe(twin,{"task":ctx.get("text","probe")}); h=twin_health(twin)
  return {"twin":twin,"health":h}
 return _safe("mem20twinz", run)

def output_compile_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20agentoutputcompilerz.domain import merge_outputs, validate_output
  except Exception: from mem20agentoutputcompilerz.mem20agentoutputcompilerz.domain import merge_outputs, validate_output
  o=[{"text":ctx.get("text",""),"ok":True}]; return {"merged":merge_outputs(o),"valid":validate_output(o[0])}
 return _safe("mem20agentoutputcompilerz", run)

def episodic_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20episodicmemorygraphz.domain import create_episode, add_event
  except Exception: from mem20episodicmemorygraphz.mem20episodicmemorygraphz.domain import create_episode, add_event
  ep=create_episode("task-capture",[{"type":"capture","modality":ctx.get("modality")}]); add_event(ep,{"type":"structured","ok":True})
  return {"episode_id":ep.get("id") if isinstance(ep,dict) else None}
 return _safe("mem20episodicmemorygraphz", run)

def capture_signals(ctx:Mapping[str,Any]|None=None)->Dict[str,Any]:
 c=dict(ctx or {"text":"probe","modality":"text"})
 checks={"modality_bridge":modality_bridge_signal(c),"sensory_ingest":sensory_ingest_signal(c),"intent_compile":intent_compile_signal(c),"task_capture_personal":task_capture_personal_signal(c),"output_compile":output_compile_signal(c),"episodic":episodic_signal(c)}
 reachable=[k for k,v in checks.items() if v.get("ok")]
 return {"ok":len(reachable)==6,"count":len(reachable),"reachable":reachable,"checks":checks}
def probe()->Dict[str,Any]: return capture_signals()
