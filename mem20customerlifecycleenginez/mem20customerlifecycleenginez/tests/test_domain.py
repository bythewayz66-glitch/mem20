import importlib
MOD="mem20customerlifecycleenginez"
def _m(): return importlib.import_module(MOD+".domain")
def test_stage(): m=_m(); assert m.lifecycle_stage({"days_since_signup":3,"purchases":0})=="onboarding"
def test_transition(): m=_m(); assert m.transition({"days_since_signup":30,"purchases":2},"purchase")=="active"
def test_retention(): m=_m(); assert 0<=m.retention_probability({"engagement":0.8,"recency_days":10})<=1
def test_ltv(): m=_m(); assert m.lifetime_value({"avg_order_value":50,"purchase_frequency":2,"expected_lifespan_months":12})==1200
def test_segment(): m=_m(); r=m.segment_customers([{"id":"a","days_since_signup":3,"purchases":0}]); assert "onboarding" in r
