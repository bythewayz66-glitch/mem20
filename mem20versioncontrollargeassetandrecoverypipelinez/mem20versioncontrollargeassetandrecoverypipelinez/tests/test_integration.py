"""Tests for the RM-239 cross-module integration layer.

These are the tests that make criterion 6 real: each one calls a function from
another mem20 module on a path this subsystem actually executes, rather than
merely importing it.
"""
import importlib
import os
import tempfile

MOD = "mem20versioncontrollargeassetandrecoverypipelinez"


def _integration():
    return importlib.import_module(MOD + ".integration")


def _store():
    return tempfile.mkdtemp(prefix="rm239-test-")


def test_screen_metadata_flags_credential():
    m = _integration()
    findings = m.screen_metadata({"token": "ghp_" + "a" * 36, "artist": "kim"})
    assert len(findings) == 1
    assert findings[0]["key"] == "token"
    assert findings[0]["severity"] == "critical"
    assert findings[0]["kind"] == "credential"


def test_screen_metadata_ignores_plain_fields():
    m = _integration()
    assert m.screen_metadata({"artist": "kim", "note": "hand painted"}) == []


def test_audit_asset_release_clean_asset_is_ok():
    m = _integration()
    result = m.audit_asset_release(
        "hero_sword",
        "blade-v1",
        family="weapon",
        triangles=3000,
        metadata={"artist": "kim"},
        store_dir=_store(),
    )
    assert result["ok"] is True
    assert result["ledger"]["ok"] is True
    assert result["budget"]["ok"] is True
    assert result["integrity"]["ok"] is True
    assert result["inventory"]["subsystem_registered"] is True


def test_audit_asset_release_blocks_on_credential():
    m = _integration()
    result = m.audit_asset_release(
        "hero_sword",
        "blade-v1",
        family="weapon",
        triangles=3000,
        metadata={"api_key": "sk-" + "b" * 40},
        store_dir=_store(),
    )
    assert result["ok"] is False
    assert result["secrets"][0]["severity"] == "critical"


def test_audit_asset_release_reports_budget_violation():
    m = _integration()
    result = m.audit_asset_release(
        "boss_rig",
        "rig-v1",
        family="boss",
        triangles=1,
        store_dir=_store(),
    )
    assert result["budget"]["ok"] is False
    assert "floor" in result["budget"]["reason"]
    assert result["ok"] is False


def test_audit_asset_release_uses_memory_engine_roundtrip():
    m = _integration()
    result = m.audit_asset_release(
        "prop_crate", "crate-v1", family="prop", triangles=500, store_dir=_store()
    )
    # mem20verify.dataintegrity.check ran against the real memory_engine
    assert result["integrity"]["checked"] >= 1
    assert result["integrity"]["roundtrip_ok"] == result["integrity"]["checked"]
    # toolchest.catalog.load_inventory read the real estate inventory
    assert result["inventory"]["entries"] > 0


def test_recover_asset_records_recovery():
    m = _integration()
    domain = importlib.import_module(MOD + ".domain")
    os.environ["MEM20_STORE_PATH"] = _store()
    v1 = domain.version_asset("a1", "c1")
    v2 = domain.version_asset("a1", "c2")
    out = m.recover_asset([v1, v2], v1["version"])
    assert out["recovered"] is True
    assert out["version"]["hash"] == v1["hash"]


def test_recover_asset_missing_version():
    m = _integration()
    out = m.recover_asset([], "deadbeef")
    assert out["recovered"] is False
