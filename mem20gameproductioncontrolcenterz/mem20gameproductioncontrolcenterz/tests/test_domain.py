import importlib
MOD="mem20gameproductioncontrolcenterz"
def _m(): return importlib.import_module(MOD+".domain")
def test_sprint(): m=_m(); r=m.sprint_plan([{"id":"t1","effort":3},{"id":"t2","effort":4}],5); assert len(r)>=1
def test_burndown(): m=_m(); r=m.burndown([{"id":"t1","effort":3}],["t1"]); assert r["done"]==3
def test_milestone(): m=_m(); r=m.milestone_status([{"id":"m1","due_day":5}],3); assert r[0]["status"]=="on_track"
def test_risk(): m=_m(); assert 0<=m.risk_score({"scope_creep":True,"team_size":2,"budget_ratio":1.2})<=1
def test_health(): m=_m(); assert m.production_health([{"done":True},{"done":False}])==0.5
