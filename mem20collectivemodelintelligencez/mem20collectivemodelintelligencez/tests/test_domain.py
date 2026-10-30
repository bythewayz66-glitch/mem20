import importlib
MOD="mem20collectivemodelintelligencez"
def _m(): return importlib.import_module(MOD+".domain")
def test_ensemble(): m=_m(); assert m.ensemble_predict([1.0,2.0,3.0])==2.0
def test_diversity(): m=_m(); assert 0<=m.diversity_score(["a","b","a"])<=1
def test_distill(): m=_m(); assert m.knowledge_distill([1.0,2.0],[1.1,1.9])>=0
def test_conf(): m=_m(); assert m.aggregate_confidence([0.8,0.9])==0.85
def test_classify(): m=_m(); assert m.ensemble_predict(["a","b","a"])=="a"
