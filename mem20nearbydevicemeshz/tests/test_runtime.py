from mem20nearbydevicemeshz.runtime import Engine, load_config

def test_simulate_all_pass():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    res = eng.simulator()
    assert all(v.get('ok') for v in res.values()), res

def test_discover():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'devices': [{'id':'a','capabilities':['cpu'],'trust':0.9,'distance_m':1.0},{'id':'b','capabilities':['gpu'],'trust':0.4,'distance_m':2.0}]})
    assert 'combined_capabilities' in out
    assert 'cpu' in out['combined_capabilities']
    assert out['trusted_count'] == 1

def test_signature_mode():
    cfg = load_config('CAPABILITY.json')
    eng = Engine(cfg)
    out = eng.execute({'signature_mode': True})
    assert 'cooperative_computer' in out
