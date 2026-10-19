"""Double-auction price-time matching for inference capacity.

Tests exercise the real behaviour, not the wiring.
"""
import importlib, math
import pytest

MOD = "mem20adaptiveinferencemarketplacez"


def _m():
    return importlib.import_module(MOD + ".domain")



def _o(price, ts, side, qty, oid):
    return _m().Order(price=price, ts=ts, side=side, qty=qty, oid=oid)


def test_crossing_orders_match():
    m = _m()
    res = m.match([_o(10.0, 1, "buy", 5, "b1"), _o(9.0, 2, "sell", 5, "s1")])
    assert res["fill_count"] == 1
    assert res["fills"][0]["qty"] == 5
    assert res["matched_volume"] == 5


def test_uncrossed_book_does_not_match():
    m = _m()
    res = m.match([_o(8.0, 1, "buy", 5, "b1"), _o(9.0, 2, "sell", 5, "s1")])
    assert res["fill_count"] == 0
    assert res["clearing_price"] is None


def test_price_time_priority_takes_best_price_first():
    m = _m()
    res = m.match([_o(9.0, 1, "buy", 5, "b_low"),
                   _o(11.0, 2, "buy", 5, "b_best"),
                   _o(10.0, 3, "sell", 10, "s1")])
    assert res["fills"][0]["buy_oid"] == "b_best"
    assert res["resting_bids"] == 5


def test_partial_fill_leaves_resting_liquidity():
    m = _m()
    res = m.match([_o(10.0, 1, "buy", 3, "b1"), _o(9.0, 2, "sell", 10, "s1")])
    assert res["matched_volume"] == 3
    assert res["resting_asks"] == 7

