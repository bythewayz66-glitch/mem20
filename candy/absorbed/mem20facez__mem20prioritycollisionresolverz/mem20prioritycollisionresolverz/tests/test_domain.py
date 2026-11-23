"""Priority arbitration with aging, so nothing starves."""
import importlib
MOD = "mem20prioritycollisionresolverz"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_highest_priority_served_first():
    r = _m().PriorityCollisionResolver()
    r.submit("low", 1); r.submit("high", 10)
    assert r.resolve(1)[0][0] == "high"


def test_empty_resolves_to_nothing():
    assert _m().PriorityCollisionResolver().resolve(5) == []


def test_resolve_count_limits_output():
    r = _m().PriorityCollisionResolver()
    for i in range(10):
        r.submit(i, i)
    assert len(r.resolve(4)) == 4


def test_aging_rate_cannot_be_negative():
    import pytest
    with pytest.raises(ValueError):
        _m().PriorityCollisionResolver(aging_rate=-1)


def test_depth_tracks_pending_work():
    r = _m().PriorityCollisionResolver()
    for i in range(7):
        r.submit(i, 1)
    assert r.depth == 7
    r.resolve(3)
    assert r.depth == 4
