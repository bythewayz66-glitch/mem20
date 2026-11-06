import importlib
import tempfile

MOD = "mem20assetintakecatalogingandvalidationpipelinez"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_validate():
    m = _m()
    r = m.validate_asset({"id": "a", "type": "image", "format": "png"})
    assert r["valid"] is True


def test_catalog():
    m = _m()
    r = m.catalog_asset({"id": "a", "type": "image", "format": "png", "size_bytes": 100})
    assert r["id"] == "a"


def test_intake():
    m = _m()
    r = m.intake_pipeline([{"id": "a", "type": "image", "format": "png"}])
    assert r["valid"] == 1


def test_search():
    m = _m()
    cat = [{"id": "a", "type": "image", "tags": ["ui"]}]
    r = m.search_catalog(cat, "ui")
    assert len(r) == 1


def test_dedupe():
    m = _m()
    r = m.dedupe_assets([{"id": "a"}, {"id": "a"}])
    assert len(r) == 1


def test_estate_context_real_integrations():
    m = _m()
    with tempfile.TemporaryDirectory() as d:
        ctx = m.estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
