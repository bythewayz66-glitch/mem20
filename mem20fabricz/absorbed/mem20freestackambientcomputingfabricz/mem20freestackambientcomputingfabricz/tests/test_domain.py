import importlib
MOD="mem20freestackambientcomputingfabricz"
def _m(): return importlib.import_module(MOD+".domain")
def test_pool(): m=_m(); r=m.pool_resources([{"cpu":4,"memory":8,"storage":100}]); assert r["cpu"]==4
def test_discover(): m=_m(); f={"services":[{"capabilities":["x"]}]}; r=m.discover_services(f,"x"); assert len(r)==1
def test_alloc(): m=_m(); f={"pool":{"cpu":10,"memory":10}}; r=m.allocate(f,{"cpu":2,"memory":2}); assert r["allocated"] is True
def test_health(): m=_m(); f={"nodes":[{"status":"online"},{"status":"offline"}]}; r=m.fabric_health(f); assert r["health"]==0.5
def test_score(): m=_m(); f={"pool":{"cpu":5},"total_cpu":10}; assert m.ambient_score(f)==0.5
