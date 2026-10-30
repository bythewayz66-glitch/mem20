import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mem20crisisresponsemeshz.runtime import Engine, load_config

def test_simulate_all_pass():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    res = eng.simulator()
    assert all(v.get('ok') for v in res.values()), res

def test_crisis_execute():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'text': 'db outage', 'severity': 'critical'})
    assert out['containment'] == 'immediate'
    assert out['incidents'][0]['lead'] is not None

def test_signature_mode_opt_in():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'signature_mode': True})
    assert 'instant_incident_team' in out
    assert out['instant_incident_team']['formed_in_seconds'] == 1

def test_benchmark():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    b = eng.benchmark(20)
    assert b['iterations'] == 20
