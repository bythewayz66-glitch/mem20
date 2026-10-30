import importlib
MOD="mem20gameplaysystemsdataandbalancepipelinez"
def _m(): return importlib.import_module(MOD+".domain")
def test_collect(): m=_m(); r=m.collect_telemetry([{"player":"a"}]); assert r["events"]==1
def test_agg(): m=_m(); r=m.aggregate_metrics({"raw":[{"action":"jump"},{"action":"jump"}]}); assert r["action_counts"]["jump"]==2
def test_tuning(): m=_m(); r=m.balance_tuning({"hp":10}, {"hp":15}); assert len(r)==1
def test_funnel(): m=_m(); r=m.funnel_analysis([{"name":"a","count":100},{"name":"b","count":50}]); assert r[0]["conversion"]==0.5
def test_pipeline(): m=_m(); r=m.pipeline_report([{"valid":True},{"valid":False}]); assert r["valid"]==1
