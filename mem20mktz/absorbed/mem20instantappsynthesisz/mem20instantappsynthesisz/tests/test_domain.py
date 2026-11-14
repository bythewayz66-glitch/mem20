import importlib
MOD="mem20instantappsynthesisz"
def _m(): return importlib.import_module(MOD+".domain")
def test_synth(): m=_m(); r=m.synthesize({"name":"app","pages":["home"],"components":["btn"]}); assert r["name"]=="app"
def test_scaffold(): m=_m(); r=m.scaffold({"files":["a.jsx"]}); assert "src" in r["dirs"]
def test_size(): m=_m(); r=m.estimate_size({"pages":["home","about"],"components":["btn"]}); assert r>0
def test_validate(): m=_m(); r=m.validate_spec({"name":"app"}); assert r["valid"] is True
def test_deploy(): m=_m(); r=m.deploy_config({"name":"app"},"vercel"); assert r["target"]=="vercel"
