"""Token-bucket and leaky-bucket rate limiting."""
import importlib
import pytest
MOD = "mem20autonomoustrafficcontrollerz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_invalid_rates_refuse():
    import pytest
    with pytest.raises(ValueError):
        _m().TokenBucket(0)
    with pytest.raises(ValueError):
        _m().LeakyBucket(-1)


def test_empty_bucket_allows_a_burst_up_to_capacity():
    b = _m().TokenBucket(rate_per_sec=1, capacity=5)
    allowed = [b.allow(now=0.0) for _ in range(5)]
    assert all(allowed)


def test_bucket_refuses_once_capacity_exhausted():
    b = _m().TokenBucket(rate_per_sec=1, capacity=2)
    assert b.allow(now=0.0) and b.allow(now=0.0)
    assert b.allow(now=0.0) is False


def test_bucket_refills_at_the_configured_rate():
    b = _m().TokenBucket(rate_per_sec=10, capacity=10)
    for _ in range(10):
        b.allow(now=0.0)
    assert b.allow(now=0.0) is False
    assert b.allow(now=1.0) is True      # 1s * 10/s refilled the bucket


def test_refill_never_exceeds_capacity():
    b = _m().TokenBucket(rate_per_sec=5, capacity=3)
    b.allow(now=0.0)
    b.allow(now=1000.0)                   # a very long idle period
    assert b.tokens <= 3.0 + 1e-6


def test_retry_after_is_positive_when_refused():
    b = _m().TokenBucket(rate_per_sec=2, capacity=1)
    b.allow(now=0.0); b.allow(now=0.0)
    assert b.retry_after(now=0.0) > 0


def test_leaky_bucket_has_no_burst_allowance():
    l = _m().LeakyBucket(rate_per_sec=2)
    assert l.allow(cost=2.0, now=0.0) is True
    assert l.allow(cost=1.0, now=0.0) is False


def test_leaky_bucket_drains_over_time():
    l = _m().LeakyBucket(rate_per_sec=4)
    l.allow(cost=4.0, now=0.0)
    assert l.drain_time(now=0.0) == pytest.approx(1.0)
    assert l.drain_time(now=1.0) == pytest.approx(0.0)
