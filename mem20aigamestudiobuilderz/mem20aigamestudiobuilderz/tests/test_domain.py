import importlib
import tempfile

MOD = "mem20aigamestudiobuilderz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_scaffold():
    m = _m()
    r = m.scaffold_project("g", "rpg", "unity")
    assert "Assets" in r["folders"]


def test_asset_pipeline():
    m = _m()
    r = m.asset_pipeline([{"id": "a", "type": "texture", "format": "png"}])
    assert r["valid_count"] == 1


def test_build_config():
    m = _m()
    r = m.build_config({"name": "g"}, "mobile")
    assert r["compression"] == "lz4"


def test_estimate_size():
    m = _m()
    assert m.estimate_size([{"size_mb": 10}]) > 10


def test_validate():
    m = _m()
    r = m.validate_project({"name": "g", "genre": "rpg", "engine": "unity"})
    assert r["valid"] is True


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
