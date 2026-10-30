import importlib
MOD="mem20counterfactualmemorysimulatorz"
def _m(): return importlib.import_module(MOD+".domain")
def test_branch(): m=_m(); r=m.branch({"state":{"x":1}},{"x":2}); assert r["state"]["x"]==2
def test_replay(): m=_m(); r=m.replay({"state":{"x":0}},[{"x":1},{"x":2}]); assert len(r)==3
def test_cf(): m=_m(); r=m.counterfactual({"state":{"x":1}},{"change":{"x":2}}); assert r["state"]["x"]==2
def test_compare(): m=_m(); r=m.compare({"state":{"x":1}},{"state":{"x":2}}); assert "x" in r
def test_prob(): m=_m(); assert 0<=m.outcome_probability({"base_rate":0.5},{"effect":0.2})<=1
