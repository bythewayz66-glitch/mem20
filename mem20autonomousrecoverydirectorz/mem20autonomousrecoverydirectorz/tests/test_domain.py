import importlib
import tempfile

MOD = "mem20autonomousrecoverydirectorz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_triage():
    m = _m()
    r = m.triage({"severity": "critical"})
    assert r["priority"] == 1


def test_rollback():
    m = _m()
    r = m.rollback_plan({"version": 2}, {"version": 1})
    assert "steps" in r


def test_remediate():
    m = _m()
    r = m.remediate({}, [{"safe": True}, {"safe": False}])
    assert len(r["applied"]) == 1


def test_time():
    m = _m()
    assert m.recovery_time({"severity": "low"}) == 60


def test_health():
    m = _m()
    assert 0 <= m.health_after({"success_rate": 0.8}) <= 1


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
