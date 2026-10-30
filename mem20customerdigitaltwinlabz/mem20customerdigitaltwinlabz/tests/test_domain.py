import importlib
MOD="mem20customerdigitaltwinlabz"
def _m(): return importlib.import_module(MOD+".domain")
def test_build(): m=_m(); t=m.build_twin({"id":"u1","ltv":500}); assert t["id"]=="u1"
def test_sim(): m=_m(); t=m.build_twin({"id":"u1","behavior":{"engagement":0.8}}); r=m.simulate_behavior(t,{"steps":3,"seed":1}); assert len(r)==3
def test_churn(): m=_m(); t=m.build_twin({"id":"u1","behavior":{"engagement":0.2,"recency_days":60}}); assert 0<=m.predict_churn(t)<=1
def test_recommend(): m=_m(); t=m.build_twin({"id":"u1","ltv":2000,"behavior":{"engagement":0.9,"recency_days":5}}); assert m.recommend_action(t) in ("retention_offer","upsell","nurture")
def test_acc(): m=_m(); t=m.build_twin({"id":"u1","behavior":{"engagement":0.5,"recency_days":30},"ltv":100}); assert 0<=m.twin_accuracy(t,{"churned":False})<=1
