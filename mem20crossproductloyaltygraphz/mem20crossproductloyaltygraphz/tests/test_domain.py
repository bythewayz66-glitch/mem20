import importlib
MOD="mem20crossproductloyaltygraphz"
def _m(): return importlib.import_module(MOD+".domain")
def test_edge(): m=_m(); g=m.add_edge({}, "a","b"); assert "a" in g
def test_degree(): m=_m(); g=m.add_edge({}, "a","b"); assert m.degree(g,"a")==1
def test_centrality(): m=_m(); g=m.add_edge({}, "a","b"); r=m.centrality(g); assert "a" in r
def test_recommend(): m=_m(); g=m.add_edge({}, "a","b"); r=m.recommend_products(g,["a"]); assert "b" in r
def test_loyalty(): m=_m(); g=m.add_edge({}, "a","b"); assert m.loyalty_score(["a"],g)>=0
