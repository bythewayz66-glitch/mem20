import importlib
MOD="mem20reversibleexecutiongraphz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); r=m.create_graph(); assert r["nodes"]==[]
def test_add(): m=_m(); r=m.create_graph(); m.add_node(r,"n1"); assert "n1" in r["nodes"]
def test_undo(): m=_m(); r=m.create_graph(); m.add_node(r,"n1"); m.undo(r); assert "n1" not in r["nodes"]
def test_redo(): m=_m(); r=m.create_graph(); m.add_node(r,"n1"); m.undo(r); m.redo(r); assert "n1" in r["nodes"]
def test_health(): m=_m(); r=m.create_graph(); assert "nodes" in m.graph_health(r)
