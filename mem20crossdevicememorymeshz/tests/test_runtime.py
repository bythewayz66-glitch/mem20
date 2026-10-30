import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mem20crossdevicememorymeshz.runtime import Engine, load_config

def test_simulate_all_pass():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    res = eng.simulator()
    assert all(v.get('ok') for v in res.values()), res

def test_sync():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'text': 'sync', 'memories': [{'id':'m1','content':'a','tags':['work'],'updated':1},{'id':'m2','content':'b','tags':['personal'],'updated':2}], 'selective_tags': ['work']})
    assert out['replicated'] == 1
    assert out['merged_count'] == 1

def test_signature_mode():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'signature_mode': True})
    assert 'continuity_follows_user' in out

def test_benchmark():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    b = eng.benchmark(20)
    assert b['iterations'] == 20
