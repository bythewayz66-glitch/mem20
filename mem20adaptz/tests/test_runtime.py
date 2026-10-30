import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mem20adaptz.runtime import MasterEngine

def test_list_adaptives():
    eng = MasterEngine()
    assert len(eng.engines) == 6

def test_simulate_all():
    eng = MasterEngine()
    res = eng.simulate()
    assert len(res) == 6

def test_execute_all():
    eng = MasterEngine()
    out = eng.execute({"text": "demo"})
    assert "results" in out
    assert len(out["results"]) == 6

def test_execute_only():
    eng = MasterEngine()
    out = eng.execute({"text": "demo"}, only="achievement")
    assert list(out["results"].keys()) == ["achievement"]

def test_benchmark():
    eng = MasterEngine()
    b = eng.benchmark(5)
    assert len(b) == 6

def test_signatures():
    eng = MasterEngine()
    s = eng.signature_modes()
    assert len(s) == 6
