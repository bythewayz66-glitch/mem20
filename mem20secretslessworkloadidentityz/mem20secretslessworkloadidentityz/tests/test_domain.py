import importlib
MOD="mem20secretslessworkloadidentityz"
def _m(): return importlib.import_module(MOD+".domain")
def test_issue(): m=_m(); r=m.issue_identity("w1"); assert r["workload"]=="w1"
def test_verify(): m=_m(); r=m.issue_identity("w1"); assert m.verify(r)["valid"] is True
def test_rotate(): m=_m(); r=m.issue_identity("w1"); r2=m.rotate(r); assert r2["workload"]=="w1"
def test_health(): m=_m(); r=m.issue_identity("w1"); assert m.identity_health([r])["valid"]==1
