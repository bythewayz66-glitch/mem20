import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from mem20selfhealingconnectormeshz.runtime import Engine, load_config

def test_simulate_all_pass():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    res = eng.simulator()
    assert all(v.get('ok') for v in res.values()), res

def test_selfheal():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'connectors': [{'id':'c1','healthy':False},{'id':'c2','healthy':True}]})
    assert out['failed'] == 1
    assert out['actions'][0]['repaired'] is True

def test_signature_mode():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'signature_mode': True})
    assert 'auto_heal' in out

def test_benchmark():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    b = eng.benchmark(20)
    assert b['iterations'] == 20
