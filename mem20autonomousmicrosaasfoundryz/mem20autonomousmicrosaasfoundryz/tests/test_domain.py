import importlib
import tempfile

MOD = "mem20autonomousmicrosaasfoundryz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_score():
    m = _m()
    assert 0 <= m.score_idea({"market_size": 1000, "competition": 2, "effort": 3}) <= 1


def test_mvp():
    m = _m()
    r = m.mvp_spec({"name": "x", "features": ["a", "b", "c", "d"], "effort": 3})
    assert len(r["core_features"]) == 3


def test_launch():
    m = _m()
    r = m.launch_plan({"price": 9})
    assert "phases" in r


def test_revenue():
    m = _m()
    r = m.revenue_projection(100, 10)
    assert r["mrr"] == 1000


def test_rank():
    m = _m()
    r = m.idea_ranking([
        {"market_size": 100, "competition": 2, "effort": 2},
        {"market_size": 1000, "competition": 1, "effort": 1},
    ])
    assert len(r) == 2


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
