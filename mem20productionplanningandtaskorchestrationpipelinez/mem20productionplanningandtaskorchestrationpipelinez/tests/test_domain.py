import importlib
MOD="mem20productionplanningandtaskorchestrationpipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_plan(): m=_m(); r=m.create_plan([{"id":"t1","effort":3,"priority":5},{"id":"t2","effort":4,"priority":1}],5); assert len(r["scheduled"])>=1
def test_orch(): m=_m(); r=m.orchestrate([{"id":"t1"}],["a1","a2"]); assert r[0]["agent"]=="a1"
def test_bn(): m=_m(); r=m.bottleneck([{"effort":2},{"effort":5}]); assert r["effort"]==5
def test_health(): m=_m(); r=m.pipeline_health([{"status":"done"},{"status":"pending"}]); assert r["done"]==1
