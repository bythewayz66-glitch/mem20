"""Energy-aware scheduling under a hard power budget."""
import importlib
import pytest
MOD = "mem20batteryawareagentschedulerz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_unknown_hour_is_refused():
    s = _m().BatteryAwareAgentScheduler(100, {0: 1.0})
    import pytest
    with pytest.raises(KeyError):
        s.cost(1, 99)


def test_budget_must_be_positive():
    import pytest
    with pytest.raises(ValueError):
        _m().BatteryAwareAgentScheduler(0, {0: 1.0})


def test_empty_rates_refused():
    import pytest
    with pytest.raises(ValueError):
        _m().BatteryAwareAgentScheduler(10, {})


def test_cheapest_hour_is_selected():
    s = _m().BatteryAwareAgentScheduler(100, {0: 10.0, 1: 1.0, 2: 5.0})
    assert s.cheapest_slot(5, [0, 1, 2]) == 1


def test_tie_breaks_to_earliest_hour():
    s = _m().BatteryAwareAgentScheduler(100, {0: 2.0, 1: 2.0, 2: 2.0})
    assert s.cheapest_slot(1, [2, 0, 1]) == 0


def test_infeasible_work_is_refused_not_oversubscribed():
    s = _m().BatteryAwareAgentScheduler(10, {0: 5.0, 1: 9.0})
    r = s.schedule(50, [0, 1])          # 50*5=250 > 10 budget
    assert r["scheduled"] is False
    assert "budget" in r["reason"]


def test_deferral_is_counted():
    s = _m().BatteryAwareAgentScheduler(1, {0: 10.0})
    s.schedule(100, [0]); s.schedule(100, [0])
    assert s.deferred == 2


def test_headroom_is_reported():
    s = _m().BatteryAwareAgentScheduler(100, {0: 2.0})
    r = s.schedule(10, [0])
    assert r["scheduled"] is True
    assert r["cost_watts"] == pytest.approx(20.0)
    assert r["headroom_watts"] == pytest.approx(80.0)


import pytest
