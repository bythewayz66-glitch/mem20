import importlib
MOD="mem20goaleconomyschedulerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_schedule(): m=_m(); r=m.schedule_goals([{"id":"g1","value":10,"cost":5},{"id":"g2","value":5,"cost":2}],10); assert "g1" in r["scheduled"] or "g2" in r["scheduled"]
def test_value(): m=_m(); assert m.goal_value({"value":10,"cost":2})==5.0
def test_rebalance(): m=_m(); r=m.rebalance([{"id":"g1","value":10,"cost":5}],5); assert "scheduled" in r
def test_progress(): m=_m(); assert m.progress([{"id":"g1"},{"id":"g2"}],["g1"])==0.5
def test_pq(): m=_m(); r=m.priority_queue([{"id":"a","value":5,"cost":5},{"id":"b","value":10,"cost":2}]); assert r[0]["id"]=="b"
