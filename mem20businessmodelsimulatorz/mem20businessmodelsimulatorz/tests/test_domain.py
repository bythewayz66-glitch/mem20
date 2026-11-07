import importlib
MOD="mem20businessmodelsimulatorz"
def _m(): return importlib.import_module(MOD+".domain")
def _eco(): return importlib.import_module(MOD+".ecosystem")

def test_revenue(): assert _m().revenue(100,10)==1000.0
def test_cost(): assert _m().cost(500,2,100)==700.0
def test_profit(): assert _m().profit(1000,700)==300.0
def test_margin(): assert 0.29<_m().margin(1000,700)<0.31
def test_be(): assert _m().break_even(1000,10,6)==250
def test_scenario(): s=_m().scenario_sim(100,10,500,3,0.1,3); assert len(s)==3 and s[-1]["units"]>100
def test_sens(): s=_m().sensitivity(10,100,500,3); assert "base" in s and "up" in s

def test_ecosystem_demand_signal(): r=_eco().demand_signal([50,55,60]); assert r["ok"] and r["subsystem"]=="mem20demandforecastandcapacitybrainz"; assert r["point"] is not None
def test_ecosystem_counterfactual(): r=_eco().counterfactual_scenarios({"price":10},{"effect":0.1}); assert r["ok"] and r["subsystem"]=="mem20counterfactualmemorysimulatorz"
def test_ecosystem_partnership_synergy(): r=_eco().partnership_synergy({"revenue":100,"markets":["saas"],"tech":["py"]},{"revenue":200,"markets":["saas"],"tech":["py"]}); assert r["ok"] and r["subsystem"]=="mem20acquisitionandpartnershipscoutz"; assert "synergy" in r
def test_ecosystem_lifecycle_value(): r=_eco().lifecycle_value({"tenure_months":6,"spend":100}); assert r["ok"] and r["subsystem"]=="mem20customerlifecycleenginez"
def test_ecosystem_loyalty_graph(): r=_eco().loyalty_graph(["core"]); assert r["ok"] and r["subsystem"]=="mem20crossproductloyaltygraphz"
def test_ecosystem_pipeline_signal(): r=_eco().pipeline_signal([]); assert r["ok"] and r["subsystem"]=="mem20autonomoussaleslaboratoryz"; assert "pipeline_value" in r

def test_model_report_and_probe():
    m=_m(); rep=m.model_report(); assert rep["break_even_units"] is not None and len(rep["peers"])==6
    for k,v in rep["peers"].items(): assert v["ok"] is True,(k,v.get("error"))
    assert m.probe()["ok"] and m.estate_context()["peer_count"]==6
