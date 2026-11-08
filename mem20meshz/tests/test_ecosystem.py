from mem20meshz import ecosystem

def _assert_signal(sig):
    assert isinstance(sig, dict) and "subsystem" in sig and "ok" in sig
    if not sig["ok"]:
        assert "error" in sig

def test_mesh_signals():
    _assert_signal(ecosystem.eventstream_signal({"mesh":"mem20meshz"}))
    _assert_signal(ecosystem.execution_twin_signal({"mesh":"mem20meshz"}))
    _assert_signal(ecosystem.federated_grid_signal({"mesh":"mem20meshz"}))
    _assert_signal(ecosystem.recovery_signal({"mesh":"mem20meshz"}))
    _assert_signal(ecosystem.counterfactual_signal({"mesh":"mem20meshz"}))
    _assert_signal(ecosystem.protocol_discovery_signal({"mesh":"mem20meshz"}))
    r = ecosystem.mesh_signals()
    assert set(r["checks"].keys()) == {"eventstream","execution_twin","federated_grid","recovery","counterfactual","protocol_discovery"}
    for v in r["checks"].values(): _assert_signal(v)
