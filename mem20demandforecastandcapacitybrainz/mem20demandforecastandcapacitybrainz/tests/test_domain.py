"""Demand forecast with an honest prediction interval."""
import importlib
import pytest
MOD = "mem20demandforecastandcapacitybrainz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_no_observations_forecast_is_honest():
    f = _m().DemandForecastAndCapacityBrain().forecast()
    assert f["point"] is None
    assert "no observations" in f["note"]


def test_invalid_parameters_refused():
    import pytest
    with pytest.raises(ValueError):
        _m().DemandForecastAndCapacityBrain(alpha=0)
    with pytest.raises(ValueError):
        _m().DemandForecastAndCapacityBrain(window=1)


def test_forecast_always_carries_an_interval():
    b = _m().DemandForecastAndCapacityBrain()
    for v in [10, 12, 11, 13, 12, 14, 13, 15]:
        b.observe(v)
    f = b.forecast()
    for k in ("point", "low", "high"):
        assert f[k] is not None
    assert f["low"] <= f["point"] <= f["high"]


def test_volatile_series_gives_wider_interval_than_steady():
    m = _m()
    steady = m.DemandForecastAndCapacityBrain()
    for v in [10] * 12:
        steady.observe(v)
    volatile = m.DemandForecastAndCapacityBrain()
    for v in [5, 30, 2, 40, 7, 25, 3, 45]:
        volatile.observe(v)
    sw = steady.forecast()["high"] - steady.forecast()["low"]
    vw = volatile.forecast()["high"] - volatile.forecast()["low"]
    assert vw > sw, (vw, sw)


def test_longer_horizon_widens_the_interval():
    b = _m().DemandForecastAndCapacityBrain()
    for v in [10, 14, 9, 13, 11, 15, 8, 12]:
        b.observe(v)
    one = b.forecast(steps=1); four = b.forecast(steps=4)
    assert (four["high"] - four["low"]) > (one["high"] - one["low"])


def test_capacity_scales_with_service_level():
    b = _m().DemandForecastAndCapacityBrain()
    for v in [10, 12, 11, 13, 12, 14, 13, 15]:
        b.observe(v)
    lo = b.capacity_for(0.90); hi = b.capacity_for(0.99)
    assert hi > lo
