import importlib
MOD="mem20predictiverecallenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_predict(): m=_m(); r=m.predict_next(["a","b","a"],["a","b","c"]); assert r[0]=="a"
def test_score(): m=_m(); r=m.recall_score("a",{"recency":{"a":0.5},"frequency":{"a":0.8}}); assert 0<=r<=1
def test_prefetch(): m=_m(); r=m.prefetch(["a","b","c"],2); assert len(r)==2
def test_hit(): m=_m(); assert m.cache_hit_rate(8,10)==0.8
def test_health(): m=_m(); r=m.recall_health(["a","b"]); assert r["predictions"]==2
