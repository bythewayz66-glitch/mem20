import importlib
MOD="mem20modelgenomelabz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); g=m.create_genome({"id":"g1","genes":{"x":0.5}}); assert g["id"]=="g1"
def test_mutate(): m=_m(); g=m.create_genome({"id":"g1","genes":{"x":0.5}}); g2=m.mutate(g,rate=1.0,seed=1); assert g2["generation"]==1
def test_cross(): m=_m(); a=m.create_genome({"id":"a","genes":{"x":0.5}}); b=m.create_genome({"id":"b","genes":{"x":0.2}}); c=m.crossover(a,b,seed=1); assert "genes" in c
def test_fit(): m=_m(); g=m.create_genome({"id":"g1","genes":{"x":0.5}}); r=m.fitness(g,{"x":0.5}); assert 0<=r<=1
def test_evolve(): m=_m(); pop=[m.create_genome({"id":f"g{i}","genes":{"x":0.1*i}}) for i in range(4)]; r=m.evolve(pop,{"x":0.5},generations=2,seed=1); assert len(r)==4
