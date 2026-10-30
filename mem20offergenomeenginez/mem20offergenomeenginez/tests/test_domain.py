import importlib
MOD="mem20offergenomeenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_genome({"price":10,"components":["a"]}); assert "genes" in r
def test_mutate(): m=_m(); g=m.create_genome({"price":10,"components":["a"]}); g2=m.mutate(g,rate=1.0,seed=1); assert g2 is not None
def test_fit(): m=_m(); g=m.create_genome({"price":10,"components":["a"]}); r=m.fitness(g); assert 0<=r<=1
def test_evolve(): m=_m(); pop=[m.create_genome({"price":10,"components":["a"]}) for _ in range(4)]; r=m.evolve(pop,generations=2,seed=1); assert len(r)==4
