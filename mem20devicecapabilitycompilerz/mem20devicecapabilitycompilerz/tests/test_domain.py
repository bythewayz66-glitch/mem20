import importlib
MOD="mem20devicecapabilitycompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_detect(): m=_m(); c=m.detect_capabilities({"cpu_cores":4,"gpu":True,"memory_gb":8,"storage_gb":100,"network":"wifi"}); assert c["tier"]=="high"
def test_compile(): m=_m(); c=m.detect_capabilities({"cpu_cores":4,"gpu":True,"memory_gb":8}); r=m.compile_for_device("code",c); assert "gpu_rendering" in r["optimizations"]
def test_flags(): m=_m(); c=m.detect_capabilities({"cpu_cores":4,"gpu":True,"memory_gb":8}); r=m.feature_flags(c); assert r["3d_view"] is True
def test_compat(): m=_m(); c=m.detect_capabilities({"cpu_cores":2,"gpu":False,"memory_gb":2}); r=m.compatibility({"cpu_cores":2,"gpu":False,"memory_gb":2},["gpu"]); assert r["compatible"] is False
def test_low(): m=_m(); c=m.detect_capabilities({"cpu_cores":1,"gpu":False,"memory_gb":2}); assert c["tier"]=="low"
