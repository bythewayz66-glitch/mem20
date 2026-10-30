import importlib
MOD="mem20remoteexperimentlabz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_experiment("e1", {"x":1}); assert r["name"]=="e1"
def test_run(): m=_m(); r=m.create_experiment("e1", {"x":1}); m.run(r, lambda p: {"score":0.9}); assert r["status"]=="completed"
def test_compare(): m=_m(); a=m.create_experiment("a",{}); m.run(a,lambda p:{"score":0.5}); b=m.create_experiment("b",{}); m.run(b,lambda p:{"score":0.9}); r=m.compare([a,b]); assert r[0]["name"]=="b"
def test_health(): m=_m(); r=m.create_experiment("e1",{}); assert m.experiment_health([r])["total"]==1
