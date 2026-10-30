import importlib
MOD="mem20agentoutputcompilerz"
def _m(): return importlib.import_module(MOD+".domain")
def test_merge():
    m=_m(); r=m.merge_outputs([{"agent":"a","items":[1]},{"agent":"b","items":[2]}]); assert r["count"] if "count" in r else len(r["items"])==2
def test_dedupe():
    m=_m(); r=m.dedupe([{"id":1},{"id":1},{"id":2}]); assert len(r)==2
def test_compile():
    m=_m(); r=m.compile_report([{"agent":"a","items":[{"id":1}]}]); assert r["count"]==1
def test_validate():
    m=_m(); r=m.validate_output({"items":[]}); assert r["valid"] is True
def test_summarize():
    m=_m(); r=m.summarize([{"agent":"a","items":[1,2]}]); assert r["total_items"]==2
