import importlib
MOD="mem20personalautomationcanvasz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_canvas("c","u"); assert r["name"]=="c"
def test_wf(): m=_m(); r=m.create_canvas("c","u"); m.add_workflow(r,{"name":"w","steps":["s1"]}); assert len(r["workflows"])==1
def test_trigger(): m=_m(); r=m.create_canvas("c","u"); m.add_trigger(r,{"event":"x"}); assert len(r["triggers"])==1
def test_run(): m=_m(); r=m.run_workflow({"name":"w","steps":["s1"]},{}); assert r["status"]=="completed"
def test_health(): m=_m(); r=m.create_canvas("c","u"); assert m.canvas_health(r)["workflows"]==0
