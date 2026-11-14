import importlib
MOD="mem20goapagentdesignerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_plan(): m=_m(); actions=[{"name":"open","effects":{"door":"open"}}]; r=m.plan(actions,{}, {"door":"open"}); assert "open" in r
def test_cost(): m=_m(); assert m.action_cost({"cost":3})==3
def test_heuristic(): m=_m(); assert m.heuristic({"door":"closed"},{"door":"open"})==1
def test_validate(): m=_m(); actions=[{"name":"open"}]; assert m.validate_plan(["open"], actions) is True
