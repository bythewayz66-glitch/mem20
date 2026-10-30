import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mem20federatedmodellearningmeshz.runtime import Engine, load_config

def test_simulate_all_pass():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    res = eng.simulator()
    assert all(v.get('ok') for v in res.values()), res

def test_federate():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'clients': [{'id':'c1','samples':100,'update':[0.1,0.2]},{'id':'c2','samples':200,'update':[0.3,0.1]}]})
    assert out['clients'] == 2
    assert len(out['aggregated_update']) == 2

def test_signature_mode():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'signature_mode': True})
    assert 'collective_intelligence' in out

def test_benchmark():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    b = eng.benchmark(20)
    assert b['iterations'] == 20
