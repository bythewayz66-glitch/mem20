"""Circuit breaker that stops hammering a failing dependency."""
import importlib
MOD = "mem20faultcontainmentcellsz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_healthy_dependency_passes_through():
    c = _m().FaultContainmentCells()
    assert c.call(lambda: 42) == 42
    assert c.state == "closed"


def test_failures_open_the_circuit():
    c = _m().FaultContainmentCells(threshold=3)
    def boom():
        raise RuntimeError("down")
    for _ in range(3):
        try:
            c.call(boom)
        except RuntimeError:
            pass
    assert c.state == "open"


def test_open_circuit_fails_fast_without_calling():
    c = _m().FaultContainmentCells(threshold=1)
    calls = []
    def boom():
        calls.append(1); raise RuntimeError("x")
    try:
        c.call(boom)
    except RuntimeError:
        pass
    before = len(calls)
    try:
        c.call(boom)
    except Exception as e:
        assert "circuit open" in str(e)
    assert len(calls) == before, "dependency was called while open"


def test_half_open_after_cool_down_and_success_closes():
    c = _m().FaultContainmentCells(threshold=1, cool_down=10)
    try:
        c.call(lambda: 1 / 0)
    except ZeroDivisionError:
        pass
    assert c.state == "open"
    assert c.call(lambda: "probe", now=20) == "probe"
    assert c.state == "closed"


def test_failed_probe_reopens():
    c = _m().FaultContainmentCells(threshold=1, cool_down=10)
    try:
        c.call(lambda: 1 / 0)
    except ZeroDivisionError:
        pass
    try:
        c.call(lambda: 1 / 0, now=20)
    except ZeroDivisionError:
        pass
    assert c.state == "open"


def test_threshold_must_be_positive():
    import pytest
    with pytest.raises(ValueError):
        _m().FaultContainmentCells(threshold=0)
