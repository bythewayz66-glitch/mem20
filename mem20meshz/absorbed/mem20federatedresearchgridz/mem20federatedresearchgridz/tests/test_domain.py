import importlib
MOD="mem20federatedresearchgridz"
def _m(): return importlib.import_module(MOD+".domain")
def test_register(): m=_m(); g=m.register_node({"nodes":[]},{"id":"n1"}); assert len(g["nodes"])==1
def test_distribute(): m=_m(); g=m.register_node({"nodes":[]},{"id":"n1","status":"ready","load":0}); r=m.distribute_task(g,{"cost":1}); assert r["id"]=="n1"
def test_agg(): m=_m(); assert m.aggregate_results([1.0,2.0,3.0])==2.0
def test_health(): m=_m(); g=m.register_node({"nodes":[]},{"id":"n1","status":"ready"}); r=m.grid_health(g); assert r["health"]==1.0
def test_round(): m=_m(); g=m.register_node({"nodes":[]},{"id":"n1","status":"ready","load":0,"compute":2}); r=m.federated_round(g,{"size":3}); assert r["ok"] is True
