import importlib
import tempfile

MOD = "mem20autonomoussoftwarefoundryz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_spec():
    m = _m()
    r = m.spec_to_tasks({"features": ["auth", "api"]})
    assert len(r) >= 3


def test_quality():
    m = _m()
    assert m.code_quality({"tests_pass": True, "coverage": 0.9, "lint_clean": True}) == 1.0


def test_deploy():
    m = _m()
    assert m.deploy_decision(0.8) is True


def test_effort():
    m = _m()
    r = m.estimate_effort({"features": ["a", "b", "c"]})
    assert r["days"] == 6


def test_artifact():
    m = _m()
    r = m.build_artifact({"name": "app"}, "code")
    assert "checksum" in r


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
