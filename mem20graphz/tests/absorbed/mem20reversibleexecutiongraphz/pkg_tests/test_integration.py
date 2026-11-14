"""Tests for the RM-052 cross-module integration layer.

Each test calls a function from another mem20 module on a path this subsystem
actually executes, which is what criterion 6 requires.
"""
import importlib
import tempfile

MOD = "mem20reversibleexecutiongraphz"


def _integration():
    return importlib.import_module(MOD + ".integration")


def _store():
    return tempfile.mkdtemp(prefix="rm052-test-")


def _steps():
    return [
        {"id": "s1", "payload": {"op": "resize"}, "triangles": 3000},
        {"id": "s2", "payload": {"op": "retexture"}, "triangles": 4000},
    ]


def test_screen_step_flags_credential():
    m = _integration()
    findings = m.screen_step({"id": "s1", "payload": {"token": "ghp_" + "a" * 36}})
    assert len(findings) == 1
    assert findings[0]["severity"] == "critical"
    assert findings[0]["kind"] == "credential"


def test_screen_step_ignores_plain_payload():
    m = _integration()
    assert m.screen_step({"id": "s1", "payload": {"op": "resize"}}) == []


def test_execute_plan_is_reversible():
    m = _integration()
    result = m.execute_reversible_plan("p1", _steps(), family="prop", store_dir=_store())
    assert result["reversible"] is True
    assert result["ok"] is True
    assert result["health"]["nodes"] == 2
    assert result["ledger"]["ok"] is True
    assert result["integrity"]["ok"] is True
    assert result["inventory"]["subsystem_registered"] is True


def test_execute_plan_refuses_credential_step():
    m = _integration()
    steps = _steps() + [{"id": "s3", "payload": {"api_key": "sk-" + "b" * 40}}]
    result = m.execute_reversible_plan("p2", steps, store_dir=_store())
    assert result["refused"] == ["s3"]
    assert result["reversible"] is False
    assert result["ok"] is False


def test_execute_plan_refuses_budget_violation():
    m = _integration()
    steps = [{"id": "s1", "payload": {"op": "resize"}, "triangles": 1}]
    result = m.execute_reversible_plan("p3", steps, family="boss", store_dir=_store())
    assert result["refused"] == ["s1"]
    assert "floor" in result["budgets"][0]["reason"]


def test_execute_plan_uses_memory_engine_roundtrip():
    m = _integration()
    result = m.execute_reversible_plan("p4", _steps(), store_dir=_store())
    # mem20verify.dataintegrity.check ran against the real memory_engine
    assert result["integrity"]["checked"] >= 1
    assert result["integrity"]["roundtrip_ok"] == result["integrity"]["checked"]
    # toolchest.catalog.load_inventory read the real estate inventory
    assert result["inventory"]["entries"] > 0


def test_rollback_plan_undoes_everything():
    m = _integration()
    result = m.rollback_plan("p5", _steps(), store_dir=_store())
    assert result["undone"] == 2
    assert result["remaining"] == 0
    assert result["clean"] is True


def test_rollback_plan_empty_is_clean():
    m = _integration()
    result = m.rollback_plan("p6", [], store_dir=_store())
    assert result["undone"] == 0
    assert result["clean"] is True
