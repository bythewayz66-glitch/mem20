"""6 unique peers for Narrative/Dialogue/Localization Pipeline (#339). Different set from #332."""
from __future__ import annotations
from typing import Any, Callable, Dict, Mapping
def _safe(name:str,fn:Callable[[],Dict[str,Any]])->Dict[str,Any]:
 try:
  res=fn(); out={"ok":True,"subsystem":name}
  if isinstance(res,dict): out.update(res)
  else: out["result"]=res
  return out
 except Exception as e: return {"ok":False,"subsystem":name,"error":f"{type(e).__name__}: {e}"}

def level_world_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20pipez.domain import compile_level_plan
  except Exception: from mem20pipez.mem20pipez.domain import compile_level_plan
  r=compile_level_plan({"id":"narr-probe","stages":["blockout","navigation"],"grid":[[0,0],[0,0]],"rooms":[{"id":"r1"}]})
  return {"pipeline_status":(r.get("pipeline") or {}).get("status"),"ok_plan":r.get("ok")}
 return _safe("mem20pipez", run)

def dynamic_narrative_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20dynamicnarrativeenginez.domain import create_story, add_node, current_text
  except Exception: from mem20dynamicnarrativeenginez.mem20dynamicnarrativeenginez.domain import create_story, add_node, current_text
  s=create_story("probe"); add_node(s,{"id":"n1","text":ctx.get("text","hi")}); t=current_text(s)
  return {"story_id":(s.get("id") if isinstance(s,dict) else None),"text":t}
 return _safe("mem20dynamicnarrativeenginez", run)

def lore_content_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20loreragcontentgeneratorz.domain import generate, quality_score
  except Exception: from mem20loreragcontentgeneratorz.mem20loreragcontentgeneratorz.domain import generate, quality_score
  gen=generate({"prompt":ctx.get("text","NPC greeting"),"context":[]}); q=quality_score(gen if isinstance(gen,dict) else {"text":str(gen)})
  return {"generated":gen,"quality":q}
 return _safe("mem20loreragcontentgeneratorz", run)

def context_compression_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20rewardforgez.domain import extractive_summary, key_terms
  except Exception: from mem20rewardforgez.mem20rewardforgez.domain import extractive_summary, key_terms
  t=str(ctx.get("text","NPC: Hello. HERO: Ready.")); return {"summary":extractive_summary(t,1),"terms":key_terms(t,3)}
 return _safe("mem20rewardforgez", run)

def episodic_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20episodicmemorygraphz.domain import create_episode, recall
  except Exception: from mem20episodicmemorygraphz.mem20episodicmemorygraphz.domain import create_episode, recall
  ep=create_episode("narrative",[{"type":"dialogue","text":ctx.get("text","hi")}]); rec=recall([ep],"dialogue")
  return {"episode":ep.get("id") if isinstance(ep,dict) else None,"recall":len(rec) if isinstance(rec,list) else 1}
 return _safe("mem20episodicmemorygraphz", run)

def eventstream_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
  except Exception: from mem20eventstreamsuperhighwayz.mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
  s=create_stream("narrative"); publish(s,"localize",{"ok":True},key="n"); t=throughput(s,60)
  return {"stream":(s.get("name") if isinstance(s,dict) else "narrative"),"throughput":t}
 return _safe("mem20eventstreamsuperhighwayz", run)

def narrative_signals(ctx:Mapping[str,Any]|None=None)->Dict[str,Any]:
 c=dict(ctx or {"text":"NPC: Hello"})
 checks={"level_world":level_world_signal(c),"dynamic_narrative":dynamic_narrative_signal(c),"lore_content":lore_content_signal(c),"context_compression":context_compression_signal(c),"episodic":episodic_signal(c),"eventstream":eventstream_signal(c)}
 reachable=[k for k,v in checks.items() if v.get("ok")]
 return {"ok":len(reachable)==6,"count":len(reachable),"reachable":reachable,"checks":checks}
def probe()->Dict[str,Any]: return narrative_signals()
