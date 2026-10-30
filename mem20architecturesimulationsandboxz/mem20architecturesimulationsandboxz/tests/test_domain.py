import importlib
MOD="mem20architecturesimulationsandboxz"
def _m(): return importlib.import_module(MOD+".domain")
def test_simulate():
    m=_m(); r=m.simulate_load({"nodes":[{"id":"n1","capacity_rps":100,"count":1,"base_latency_ms":10}]},50); assert len(r)==1
def test_scaling():
    m=_m(); r=m.scaling_recommendation([{"id":"n1","utilization":0.95}]); assert r[0]["action"]=="scale_up"
def test_cost():
    m=_m(); assert m.topology_cost({"nodes":[{"count":2}]})>0
def test_bottleneck():
    m=_m(); r=m.bottleneck_node([{"id":"n1","utilization":0.5},{"id":"n2","utilization":0.9}]); assert r["id"]=="n2"
def test_chaos():
    m=_m(); r=m.chaos_test({"nodes":[{"id":"a"},{"id":"b"}]},0.5,1); assert "failed_nodes" in r
