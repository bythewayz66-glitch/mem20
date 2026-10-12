"""Ebbinghaus forgetting curve with spaced reinforcement scheduling.

Tests exercise the real behaviour, not the wiring.
"""
import importlib, math
import pytest

MOD = "mem20adaptiveforgettingenginez"


def _m():
    return importlib.import_module(MOD + ".domain")



def test_retention_follows_exponential_curve():
    m = _m()
    assert m.retention(0, 10) == pytest.approx(1.0)
    assert m.retention(10, 10) == pytest.approx(math.exp(-1), abs=1e-9)
    assert m.retention(20, 10) == pytest.approx(math.exp(-2), abs=1e-9)


def test_review_state_flip_point_is_consistent():
    m = _m()
    # At t == S the curve is exp(-1) == 0.3679, NOT 0.5. The threshold crossing
    # happens later, at t = S*ln(2). An earlier version of this test asserted
    # 0.5 and was wrong; the implementation was right.
    s = m.review_state(0, 10, now_ts=10 * 86400, threshold=0.5)
    assert s["retention"] == pytest.approx(math.exp(-1), abs=1e-6)
    cross = m.review_state(0, 10, now_ts=10 * math.log(2) * 86400, threshold=0.5)
    assert cross["retention"] == pytest.approx(0.5, abs=1e-6)
    assert cross["retrievable"] is True
    assert s["next_review_days"] == pytest.approx(10 * math.log(2), abs=0.05)


def test_reinforcement_widens_interval_and_failure_shrinks_it():
    m = _m()
    assert m.reinforce(10, success=True) == pytest.approx(18.0)
    assert m.reinforce(10, success=False) == pytest.approx(4.0)


def test_queue_is_ordered_most_lapsed_first():
    m = _m()
    now = 100 * 86400
    items = [
        {"id": "fresh", "last_review_ts": now - 1 * 86400, "stability_days": 30},
        {"id": "stale", "last_review_ts": now - 90 * 86400, "stability_days": 1},
        {"id": "mid", "last_review_ts": now - 20 * 86400, "stability_days": 10},
    ]
    q = m.review_queue(items, now_ts=now)
    assert [x["id"] for x in q["queue"]][0] == "stale"
    assert "fresh" not in [x["id"] for x in q["queue"]]

