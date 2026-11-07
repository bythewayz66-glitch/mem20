import importlib
import tempfile

MOD = "mem20causalroutingbrainz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_effect():
    m = _m()
    assert m.causal_effect([10, 12], [5, 6]) > 0


def test_route():
    m = _m()
    assert isinstance(m.route_by_cause({"x": 1}, {"x": 2}), (int, float))


def test_confounder():
    m = _m()
    assert m.confounder_adjust(1.0, 0.2) == 0.8


def test_intervention():
    m = _m()
    assert m.intervention_value(5, 8) == 3


def test_graph():
    m = _m()
    r = m.causal_graph([("a", "b")])
    assert "a" in r


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
