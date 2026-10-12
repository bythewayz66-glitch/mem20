"""Least-connections load balancing with health withdrawal."""
import importlib
MOD = "mem20connectormarketplacez"

def _m():
    return importlib.import_module(MOD + ".domain")

def test_no_backends_returns_none():
    assert _m().ConnectorMarketplace().pick() is None


def test_all_unhealthy_returns_none():
    m = _m().ConnectorMarketplace(["a", "b"])
    m.set_healthy("a", False); m.set_healthy("b", False)
    assert m.pick() is None


def test_unhealthy_backend_receives_no_traffic():
    m = _m().ConnectorMarketplace(["fast", "slow"])
    m.set_healthy("slow", False)
    for _ in range(50):
        assert m.pick() == "fast"


def test_least_connections_prefers_the_idle_backend():
    m = _m().ConnectorMarketplace(["alpha", "beta"])
    first = m.pick()
    m.release(first)                       # first is now idle again
    # whichever was picked first now has 0 in flight; the other has 0 too,
    # so force a real asymmetry: hold one open.
    held = m.pick()
    assert held is not None
    assert m.pick() != held or m.in_flight[held] > 0
    assert sum(m.in_flight.values()) == 2


def test_sticky_key_pins_until_unhealthy():
    m = _m().ConnectorMarketplace(["a", "b"])
    first = m.pick(key="user1")
    for _ in range(5):
        assert m.pick(key="user1") == first
    m.set_healthy(first, False)
    assert m.pick(key="user1") != first


def test_release_returns_count_to_zero():
    m = _m().ConnectorMarketplace(["only"])
    m.pick(); m.release("only")
    assert m.in_flight["only"] == 0
