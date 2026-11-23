"""G-Counter and PN-Counter merge without a coordinator."""
import importlib
MOD = "mem20crdtcollaborationenginez"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_gcounter_sums_across_replicas():
    c = _m().GCounter()
    c.increment("a"); c.increment("b"); c.increment("b", 4)
    assert c.value == 6


def test_gcounter_refuses_decrement():
    import pytest
    with pytest.raises(ValueError):
        _m().GCounter().increment("a", -1)


def test_merge_is_idempotent():
    m = _m()
    a, b = m.GCounter(), m.GCounter()
    a.increment("x", 3); b.increment("y", 5)
    a.merge(b).merge(b)
    assert a.value == 8


def test_merge_is_order_independent():
    m = _m()
    a, b = m.GCounter(), m.GCounter()
    a.increment("x", 3); b.increment("y", 5)
    ab = m.GCounter(dict(a.counts)).merge(m.GCounter(dict(b.counts)))
    ba = m.GCounter(dict(b.counts)).merge(m.GCounter(dict(a.counts)))
    assert ab.value == ba.value == 8


def test_pncounter_allows_decrement():
    m = _m()
    p = m.PNCounter()
    p.increment("a", 5); p.decrement("a", 2)
    assert p.value == 3


def test_pncounter_merge_converges():
    m = _m()
    p1, p2 = m.PNCounter(), m.PNCounter()
    p1.increment("a", 2); p2.decrement("b", 1)
    p1.merge(p2); p2.merge(p1)
    assert p1.value == p2.value == 1
