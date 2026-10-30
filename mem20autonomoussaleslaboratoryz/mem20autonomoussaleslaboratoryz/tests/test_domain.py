import importlib
MOD="mem20autonomoussaleslaboratoryz"
def _m(): return importlib.import_module(MOD+".domain")
def test_score(): m=_m(); assert 0<=m.lead_score({"budget":2000,"authority":True,"need":True,"timeline_days":10})<=1
def test_outreach(): m=_m(); r=m.outreach_message({"name":"Bob","email":"b@x.com"},{"subject":"Hi {name}","body":"Hello {name}"}); assert "Bob" in r["subject"]
def test_conv(): m=_m(); assert 0<=m.conversion_probability({"budget":2000,"authority":True,"need":True,"timeline_days":10},3)<=1
def test_pipeline(): m=_m(); r=m.pipeline_value([{"deal_value":1000,"budget":2000,"authority":True,"need":True,"timeline_days":10}]); assert r>=0
def test_segment(): m=_m(); r=m.segment_leads([{"budget":2000,"authority":True,"need":True,"timeline_days":10}]); assert "hot" in r
