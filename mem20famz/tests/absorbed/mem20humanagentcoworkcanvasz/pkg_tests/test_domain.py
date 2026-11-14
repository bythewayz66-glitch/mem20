import importlib
MOD="mem20humanagentcoworkcanvasz"
def _m(): return importlib.import_module(MOD+".domain")
def test_create(): m=_m(); c=m.create_canvas("c",["u1","u2"]); assert c["name"]=="c"
def test_add(): m=_m(); c=m.create_canvas("c",["u1"]); it=m.add_item(c,"u1","hi"); assert it["id"]==0
def test_turn(): m=_m(); c=m.create_canvas("c",["u1","u2"]); r=m.take_turn(c,"u1"); assert r["ok"] is True
def test_contrib(): m=_m(); c=m.create_canvas("c",["u1"]); m.add_item(c,"u1","hi"); r=m.contributions(c); assert r["u1"]==1
def test_summary(): m=_m(); c=m.create_canvas("c",["u1"]); r=m.canvas_summary(c); assert "items" in r
