"""Autonomous sales laboratory: lead scoring, outreach, conversion, and estate report."""
from __future__ import annotations
from . import ecosystem
__all__=["lead_score","outreach_message","conversion_probability","pipeline_value","segment_leads","lab_report","probe","estate_context"]

def lead_score(lead):
    score=0.0
    if lead.get("budget",0)>1000: score+=0.3
    if lead.get("authority"): score+=0.3
    if lead.get("need"): score+=0.2
    if lead.get("timeline_days",999)<=30: score+=0.2
    return round(score,3)

def outreach_message(lead, template):
    return {"to":lead.get("email"),"subject":template.get("subject","Hello").format(name=lead.get("name","")),"body":template.get("body","").format(name=lead.get("name",""))}

def conversion_probability(lead, touches):
    base=lead_score(lead); boost=min(0.3,touches*0.05); return round(min(1.0,base+boost),3)

def pipeline_value(leads):
    return round(sum(l.get("deal_value",0)*conversion_probability(l,l.get("touches",0)) for l in leads),2)

def segment_leads(leads):
    hot=[l for l in leads if lead_score(l)>=0.7]; warm=[l for l in leads if 0.4<=lead_score(l)<0.7]; cold=[l for l in leads if lead_score(l)<0.4]
    return {"hot":hot,"warm":warm,"cold":cold}

def lab_report(leads=None):
    leads=leads or [{"name":"Bob","email":"b@x.com","deal_value":5000,"budget":3000,"authority":True,"need":True,"timeline_days":20,"touches":2}]
    seg=segment_leads(leads); val=pipeline_value(leads)
    peers={
        "content_outreach": ecosystem.content_outreach("approved sales outreach"),
        "spam_guardrail": ecosystem.spam_guardrail(1.0,{"consent":True,"opt_in":True}, True),
        "demand_timing": ecosystem.demand_timing([val/1000.0 if val else 5]*5),
        "experiment_events": ecosystem.experiment_events("lab.report",{"leads":len(leads),"value":val}),
        "deal_handoff": ecosystem.deal_handoff({"price":100},{"volume":max(1,len(leads))*10}),
        "channel_routing": ecosystem.channel_routing("lead-batch",["email","chat","phone"]),
    }
    return {"ok":all(v.get("ok") for v in peers.values()),"pipeline_value":val,"segments":{k:len(v) for k,v in seg.items()},"peers":peers}

def probe(): return ecosystem.probe()
def estate_context(store_path: str | None = None): _=store_path; r=lab_report(); return {"engine_status_checked":True,"peer_count":len(r.get("peers",{})),"peers_ok":r.get("ok"),"checks":r.get("peers",{})}
