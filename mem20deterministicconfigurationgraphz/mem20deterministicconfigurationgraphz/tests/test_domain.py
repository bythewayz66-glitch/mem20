import importlib
MOD="mem20deterministicconfigurationgraphz"
def _m(): return importlib.import_module(MOD+".domain")
def test_add_node(): m=_m(); g=m.add_node({}, "n1", {"x":1}); assert "n1" in g["nodes"]
def test_edge(): m=_m(); g=m.add_node({}, "n1", {"x":1}); g=m.add_node(g, "n2", {"y":2}); m.add_edge(g,"n1","n2"); assert ("n1","n2") in g["edges"]
def test_resolve(): m=_m(); g=m.add_node({}, "n1", {"x":1}); g=m.add_node(g, "n2", {"y":2}); m.add_edge(g,"n1","n2"); r=m.resolve(g,"n2"); assert r["x"]==1 and r["y"]==2
def test_validate(): m=_m(); g=m.add_node({}, "n1", {"x":1}); r=m.validate(g); assert r["valid"] is True
def test_diff(): m=_m(); r=m.diff_configs({"a":1,"b":2},{"a":1,"b":3}); assert "b" in r
