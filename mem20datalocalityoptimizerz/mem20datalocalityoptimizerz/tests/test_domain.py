import importlib
MOD="mem20datalocalityoptimizerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_placement(): m=_m(); r=m.placement_score({"latency_ms":5,"cost_per_gb":0.05,"capacity_gb":100,"used_gb":0},{"size_gb":10}); assert r>=0
def test_optimal(): m=_m(); n={"id":"n1","latency_ms":5,"cost_per_gb":0.05,"capacity_gb":100,"used_gb":0}; r=m.optimal_placement({"size_gb":10},[n]); assert r["id"]=="n1"
def test_migration(): m=_m(); r=m.migration_cost({"size_gb":10},{"egress_cost":0.09},{"id":"d"}); assert r==0.9
def test_report(): m=_m(); r=m.locality_report([{"local":True},{"local":False}]); assert r["ratio"]==0.5
def test_rebalance(): m=_m(); n={"id":"n1","latency_ms":5,"cost_per_gb":0.05,"capacity_gb":100,"used_gb":0}; r=m.rebalance([n],[{"id":"d","size_gb":10}]); assert r["d"]=="n1"
