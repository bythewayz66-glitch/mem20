"""Dependency-ordered planning that refuses a cycle."""
import importlib
import pytest
MOD = "mem20dynamicphasereplannerz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_empty_plan_orders_to_nothing():
    assert _m().DynamicPhaseReplanner().order() == []


def test_independent_phases_keep_declaration_order():
    p = _m().DynamicPhaseReplanner()
    p.phase("design"); p.phase("build"); p.phase("test")
    assert p.order() == ["design", "build", "test"]


def test_dependencies_are_respected():
    p = _m().DynamicPhaseReplanner()
    p.phase("test", ["build"]); p.phase("build", ["design"]); p.phase("design")
    order = p.order()
    assert order.index("design") < order.index("build") < order.index("test")


def test_implicit_dependency_phase_is_created():
    p = _m().DynamicPhaseReplanner()
    p.phase("b", ["a"])          # 'a' never declared explicitly
    assert p.order() == ["a", "b"]


def test_cycle_is_refused_not_partially_ordered():
    p = _m().DynamicPhaseReplanner()
    p.phase("a", ["c"]); p.phase("b", ["a"]); p.phase("c", ["b"])
    import pytest
    with pytest.raises(ValueError) as e:
        p.order()
    assert "cycle" in str(e.value)


def test_cycle_message_names_the_loop():
    p = _m().DynamicPhaseReplanner()
    p.phase("a", ["b"]); p.phase("b", ["a"])
    cyc = p.find_cycle()
    assert cyc and cyc[0] == cyc[-1]
    assert set(cyc[:-1]) == {"a", "b"}
