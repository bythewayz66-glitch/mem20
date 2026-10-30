import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mem20offlineresiliencemeshz.runtime import Engine, load_config

def test_simulate_all_pass():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    res = eng.simulator()
    assert all(v.get('ok') for v in res.values()), res

def test_offline_queue():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'network': False, 'reconnect': False, 'operations': [{'id':'op1'},{'id':'op2'}]})
    assert out['queued'] == 2
    assert out['applied'] == 0

def test_signature_mode():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'signature_mode': True})
    assert 'resilient_mesh' in out

def test_benchmark():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    b = eng.benchmark(20)
    assert b['iterations'] == 20
