import importlib
MOD="mem20personalcognitivesearchz"
def _m(): return importlib.import_module(MOD+".domain")
def test_index(): m=_m(); idx=m.index([{"id":"d1","text":"hello world"}]); assert "hello" in idx
def test_query(): m=_m(); idx=m.index([{"id":"d1","text":"hello world"}]); docs={"d1":{"id":"d1","text":"hello world"}}; r=m.query(idx,"hello",docs); assert len(r)==1
def test_rank(): m=_m(); r=m.rank([{"text":"hello world"},{"text":"hello"}],"hello"); assert len(r)==2
def test_recall(): m=_m(); r=m.recall({},["a","b"],2); assert len(r)==2
def test_health(): m=_m(); idx=m.index([{"id":"d1","text":"hi"}]); r=m.search_health(idx); assert r["terms"]==1
