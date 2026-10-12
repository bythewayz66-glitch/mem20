"""Milestone risk that says a milestone is late while there is still time."""
import importlib
import pytest
MOD = "mem20milestoneriskpredictorz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_velocity_needs_two_points():
    p = _m().MilestoneRiskPredictor()
    p.add_point("2026-01-01", 0)
    assert p.velocity() is None
    assert "two points" in p.forecast(10)["note"]


def test_non_positive_velocity_refused():
    import pytest
    with pytest.raises(ValueError):
        _m().MilestoneRiskPredictor(ideal_velocity=0)


def test_completed_units_cannot_go_backwards():
    p = _m().MilestoneRiskPredictor()
    p.add_point("2026-01-01", 10)
    import pytest
    with pytest.raises(ValueError):
        p.add_point("2026-01-02", 5)


def test_velocity_is_computed_from_observed_span():
    p = _m().MilestoneRiskPredictor()
    p.add_point("2026-01-01", 0); p.add_point("2026-01-11", 100)
    assert p.velocity() == pytest.approx(10.0)


def test_slow_velocity_is_flagged_behind_and_at_risk():
    p = _m().MilestoneRiskPredictor(ideal_velocity=20.0)
    p.add_point("2026-01-01", 0); p.add_point("2026-01-11", 100)
    f = p.forecast(remaining_units=500)
    assert f["behind"] is True
    assert f["at_risk"] is True
    assert f["forecast_date"] is not None


def test_on_pace_velocity_is_not_at_risk():
    p = _m().MilestoneRiskPredictor(ideal_velocity=10.0)
    p.add_point("2026-01-01", 0); p.add_point("2026-01-11", 100)
    f = p.forecast(remaining_units=100)
    assert f["behind"] is False
    assert f["at_risk"] is False


import pytest
