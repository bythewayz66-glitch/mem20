"""6 unique peers for Multi-Brand Swarm (#337)."""
from __future__ import annotations
from typing import Any, Callable, Dict, Mapping
def _safe(name:str,fn:Callable[[],Dict[str,Any]])->Dict[str,Any]:
 try:
  res=fn(); out={"ok":True,"subsystem":name}
  if isinstance(res,dict): out.update(res)
  else: out["result"]=res
  return out
 except Exception as e: return {"ok":False,"subsystem":name,"error":f"{type(e).__name__}: {e}"}

def offer_assembly_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20offerassemblyfabricz.domain import create_offer, add_component, publish
  except Exception: from mem20offerassemblyfabricz.mem20offerassemblyfabricz.domain import create_offer, add_component, publish
  o=create_offer({"brand":ctx.get("brand","b1"),"id":"o1"}); add_component(o,{"id":"c1","name":"core"}); pub=publish(o)
  return {"offer":o,"published":pub}
 return _safe("mem20offerassemblyfabricz", run)

def compounding_product_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20compoundingproductecosystemz.domain import cross_sell_matrix, ecosystem_health, network_value
  except Exception: from mem20compoundingproductecosystemz.mem20compoundingproductecosystemz.domain import cross_sell_matrix, ecosystem_health, network_value
  eco={"products":[{"id":"p1","brand":ctx.get("brand","b1")}],"edges":[]}
  cs=cross_sell_matrix(eco); h=ecosystem_health(eco); nv=network_value(eco)
  return {"cross_sell":cs,"health":h,"network_value":nv}
 return _safe("mem20compoundingproductecosystemz", run)

def business_model_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20simz.domain import simulate_model, revenue, profit
  except Exception: from mem20simz.mem20simz.domain import simulate_model, revenue, profit
  sim=simulate_model({"price":10,"customers":100,"cost":3}); rev=revenue({"price":10,"customers":100}); prof=profit({"revenue":1000,"cost":300})
  return {"simulation":sim,"revenue":rev,"profit":prof}
 return _safe("mem20simz", run)

def goal_economy_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20goaleconomyschedulerz.domain import schedule_goals, priority_queue
  except Exception: from mem20goaleconomyschedulerz.mem20goaleconomyschedulerz.domain import schedule_goals, priority_queue
  goals=[{"id":"g1","value":5,"cost":1},{"id":"g2","value":3,"cost":1}]
  s=schedule_goals(goals,3); pq=priority_queue(goals)
  return {"schedule":s,"priority_queue":pq}
 return _safe("mem20goaleconomyschedulerz", run)

def eventstream_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
  except Exception: from mem20eventstreamsuperhighwayz.mem20eventstreamsuperhighwayz.domain import create_stream, publish, throughput
  s=create_stream("brandswarm"); publish(s,"campaign",{"brand":ctx.get("brand")},key="b"); t=throughput(s,60)
  return {"stream":(s.get("name") if isinstance(s,dict) else "brandswarm"),"throughput":t}
 return _safe("mem20eventstreamsuperhighwayz", run)

def capability_market_signal(ctx:Mapping[str,Any])->Dict[str,Any]:
 def run():
  try: from mem20capabilitymarketplacez.domain import CapabilityMarketplace
  except Exception: from mem20capabilitymarketplacez.mem20capabilitymarketplacez.domain import CapabilityMarketplace
  m=CapabilityMarketplace()
  listed=m.list_capabilities() if hasattr(m,"list_capabilities") else (m.list() if hasattr(m,"list") else [])
  matched=m.match({"need":"brand-ops"}) if hasattr(m,"match") else (m.find({"need":"brand-ops"}) if hasattr(m,"find") else {"market":type(m).__name__})
  return {"listed": listed if isinstance(listed,(list,dict)) else str(type(listed)), "matched": matched}
 return _safe("mem20capabilitymarketplacez", run)

def swarm_signals(ctx:Mapping[str,Any]|None=None)->Dict[str,Any]:
 c=dict(ctx or {"brand":"b1"})
 checks={"offer_assembly":offer_assembly_signal(c),"compounding_product":compounding_product_signal(c),"business_model":business_model_signal(c),"goal_economy":goal_economy_signal(c),"eventstream":eventstream_signal(c),"capability_market":capability_market_signal(c)}
 reachable=[k for k,v in checks.items() if v.get("ok")]
 return {"ok":len(reachable)==6,"count":len(reachable),"reachable":reachable,"checks":checks}
def probe()->Dict[str,Any]: return swarm_signals()
