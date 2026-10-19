"""Elasticity-fitted adaptive pricing with revenue/margin objectives.

Tests exercise the real behaviour, not the wiring.
"""
import importlib, math
import pytest

MOD = "mem20adaptivepricingbrainz"


def _m():
    return importlib.import_module(MOD + ".domain")



def test_elasticity_is_fitted_not_assumed():
    m = _m()
    # demand halves each time price doubles -> elasticity -1
    obs = [(1.0, 100.0), (2.0, 50.0), (4.0, 25.0), (8.0, 12.5)]
    r = m.recommend_price(obs)
    assert r["elasticity"] == pytest.approx(-1.0, abs=0.05)
    assert r["demand_character"] == "elastic"


def test_revenue_optimum_matches_analytic_revenue():
    m = _m()
    # with elasticity exactly -1, revenue p*(100/p) == 100 everywhere, so any
    # price in range is optimal and revenue must be flat at 100.
    r = m.recommend_price([(1.0, 100.0), (2.0, 50.0)])
    assert r["objective_value"] == pytest.approx(100.0, rel=0.05)


def test_margin_beats_revenue_when_cost_positive():
    m = _m()
    obs = [(1.0, 100.0), (2.0, 50.0), (4.0, 25.0)]
    rev = m.recommend_price(obs, objective="revenue")
    mar = m.recommend_price(obs, objective="margin", cost=0.6)
    assert mar["recommended_price"] > rev["recommended_price"]


def test_degenerate_input_is_rejected():
    m = _m()
    with pytest.raises(ValueError):
        m.recommend_price([(1.0, 10.0)])
    with pytest.raises(ValueError):
        m.recommend_price([(2.0, 10.0), (2.0, 20.0)])

