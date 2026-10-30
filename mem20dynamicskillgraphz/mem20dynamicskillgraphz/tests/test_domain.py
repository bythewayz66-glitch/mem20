import importlib
MOD="mem20dynamicskillgraphz"
def _m(): return importlib.import_module(MOD+".domain")
def test_add(): m=_m(); g=m.add_skill({}, "py", []); assert "py" in g["skills"]
def test_update(): m=_m(); g=m.add_skill({}, "py", []); m.update_proficiency(g, "py", 0.5); assert g["skills"]["py"]["proficiency"]==0.5
def test_path(): m=_m(); g=m.add_skill({}, "adv", ["basic"]); m.add_skill(g, "basic", []); r=m.learning_path(g, "adv"); assert "basic" in r and "adv" in r
def test_gap(): m=_m(); g=m.add_skill({}, "py", []); r=m.skill_gap(g, ["py"]); assert len(r)==1
def test_stats(): m=_m(); g=m.add_skill({}, "py", []); r=m.graph_stats(g); assert r["count"]==1
