import importlib
MOD="mem20selfhealingplansz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_plan(["s1","s2"]); assert len(r["steps"])==2
def test_exec(): m=_m(); r=m.create_plan(["s1"]); m.execute_step(r,0,lambda n: None); assert r["steps"][0]["status"]=="done"
def test_heal(): m=_m(); r=m.create_plan(["s1"]); m.execute_step(r,0,lambda n: (_ for _ in ()).throw(Exception("boom"))); assert r["steps"][0]["status"]=="failed"; m.heal_plan(r); assert r["steps"][0]["status"]=="pending"
def test_status(): m=_m(); r=m.create_plan(["s1"]); m.execute_step(r,0,lambda n: None); assert m.plan_status(r)["done"]==1
