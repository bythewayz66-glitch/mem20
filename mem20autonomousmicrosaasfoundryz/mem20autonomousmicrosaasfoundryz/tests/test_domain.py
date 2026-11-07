import importlib
MOD="mem20autonomousmicrosaasfoundryz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")

def test_score(): m=_m(); assert 0<=m.score_idea({"market_size":1000,"competition":2,"effort":3})<=1
def test_mvp(): m=_m(); r=m.mvp_spec({"name":"x","features":["a","b","c","d"],"effort":3}); assert len(r["core_features"])==3
def test_launch(): m=_m(); r=m.launch_plan({"price":9}); assert "phases" in r
def test_revenue(): m=_m(); r=m.revenue_projection(100,10); assert r["mrr"]==1000
def test_rank(): m=_m(); r=m.idea_ranking([{"market_size":100,"competition":2,"effort":2},{"market_size":1000,"competition":1,"effort":1}]); assert len(r)==2

def test_ecosystem_economics_real_values():
    r=_eco().economics(100,9.0); assert r["ok"] and r["subsystem"]=="mem20businessmodelsimulatorz"; assert "margin" in r
def test_ecosystem_demand_signal_real_values():
    r=_eco().demand_signal([20,25,22,30,28]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"; assert r["point"] is not None
def test_ecosystem_build_schedule_real_values():
    r=_eco().build_schedule(["core","auth"]); assert r["ok"] and r["subsystem"]=="mem20aiproductionstudiooperatingsystemz"; assert "scheduled" in r
def test_ecosystem_launch_pipeline_real_values():
    r=_eco().launch_pipeline([]); assert r["ok"] and r["subsystem"]=="mem20autonomoussaleslaboratoryz"; assert "pipeline_value" in r
def test_ecosystem_content_quality_real_values():
    r=_eco().content_quality("launch saas"); assert r["ok"] and r["subsystem"]=="mem20loreragcontentgeneratorz"; assert r["output_len"]>0
def test_ecosystem_capability_routing_real_values():
    r=_eco().capability_routing("x",["auth","billing"]); assert r["ok"] and r["subsystem"]=="mem20capabilitymarketplacez"; assert r["owner"] in ("auth","billing")

def test_foundry_report_and_probe():
    m=_m(); rep=m.foundry_report(); assert rep["idea_score"]>=0 and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True, (k,v.get("error"))
    assert m.probe()["ok"] is True and m.estate_context()["peer_count"]==6
