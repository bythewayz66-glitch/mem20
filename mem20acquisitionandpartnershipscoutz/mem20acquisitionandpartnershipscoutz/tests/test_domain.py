import importlib
import tempfile

MOD = "mem20acquisitionandpartnershipscoutz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_target_score():
    m = _m()
    s = m.target_score({"revenue": 50}, {"weights": {"revenue": 1.0}, "targets": {"revenue": 100}})
    assert 0 <= s <= 1


def test_strategic_fit():
    m = _m()
    s = m.strategic_fit({"markets": ["a"], "tech": ["x"], "revenue": 1000}, {"markets": ["a"], "tech": ["x"], "revenue": 100})
    assert 0 <= s <= 1


def test_rank():
    m = _m()
    r = m.rank_targets([{"revenue": 50}, {"revenue": 100}], {"weights": {"revenue": 1.0}, "targets": {"revenue": 100}})
    assert len(r) == 2


def test_priority():
    m = _m()
    assert m.outreach_priority({"revenue": 90}, {"weights": {"revenue": 1.0}, "targets": {"revenue": 100}}) in ("high", "medium", "low")


def test_synergy():
    m = _m()
    s = m.synergy_estimate({"markets": [], "tech": [], "revenue": 1000}, {"markets": [], "tech": [], "revenue": 100})
    assert s >= 0


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
