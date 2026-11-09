import importlib
MOD="mem20labz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); g=m.create_genome({"id":"g1","genes":{"x":0.5}}); assert g["id"]=="g1"
def test_mutate(): m=_m(); g=m.create_genome({"id":"g1","genes":{"x":0.5}}); g2=m.mutate(g,rate=1.0,seed=1); assert g2["generation"]==1
def test_cross(): m=_m(); a=m.create_genome({"id":"a","genes":{"x":0.5}}); b=m.create_genome({"id":"b","genes":{"x":0.2}}); c=m.crossover(a,b,seed=1); assert "genes" in c
def test_fit(): m=_m(); g=m.create_genome({"id":"g1","genes":{"x":0.5}}); r=m.fitness(g,{"x":0.5}); assert 0<=r<=1
def test_evolve(): m=_m(); pop=[m.create_genome({"id":f"g{i}","genes":{"x":0.1*i}}) for i in range(4)]; r=m.evolve(pop,{"x":0.5},generations=2,seed=1); assert len(r)==4

from mem20labz import ecosystem
def _assert_signal(sig):
    assert isinstance(sig,dict) and "subsystem" in sig and "ok" in sig
    if not sig["ok"]: assert "error" in sig

def test_simulate_genome_lab():
    m=_m(); r=m.simulate_genome_lab({"population":4,"generations":2,"seed":1,"objective":{"quality":1.0,"latency":0.2}})
    assert r["ok"] and r["best"] and r["record"] and "ancestry" in r["record"]

def test_ecosystem():
    c={"model":"probe"}
    _assert_signal(ecosystem.runtime_compat_signal(c)); _assert_signal(ecosystem.cost_opt_signal(c)); _assert_signal(ecosystem.kernel_opt_signal(c)); _assert_signal(ecosystem.counterfactual_signal(c)); _assert_signal(ecosystem.execution_twin_signal(c)); _assert_signal(ecosystem.eventstream_signal(c))
    r=ecosystem.genome_signals(c); assert set(r["checks"].keys())=={"runtime_compat","cost_opt","kernel_opt","counterfactual","execution_twin","eventstream"}
    for v in r["checks"].values(): _assert_signal(v)
