"""Least-connections routing with sticky sessions and health."""
import importlib
import tempfile

MOD = "mem20connectormarketplacez"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_empty_router_returns_none():
    assert _m().ConnectorMarketplace().pick() is None


def test_single_backend_receives_all_traffic():
    r = _m().ConnectorMarketplace(["only"])
    assert r.pick() == "only" and r.pick() == "only"


def test_least_connections_picks_the_lightest_backend():
    r = _m().ConnectorMarketplace(["a", "b"])
    r.pick(); r.pick(); r.pick()
    assert r.in_flight["a"] == 2 and r.in_flight["b"] == 1


def test_release_makes_room_again():
    r = _m().ConnectorMarketplace(["a", "b"])
    r.pick("x"); r.pick("y")
    r.release(r.pick())
    r.release("a")
    assert r.pick() == "a"


def test_unhealthy_backend_never_receives_traffic():
    r = _m().ConnectorMarketplace(["a", "b"])
    r.set_healthy("a", False)
    for _ in range(20):
        assert r.pick() == "b"


def test_all_unhealthy_returns_none():
    r = _m().ConnectorMarketplace(["a"])
    r.set_healthy("a", False)
    assert r.pick() is None


def test_sticky_session_pins_to_the_same_backend():
    r = _m().ConnectorMarketplace(["a", "b"])
    first = r.pick(key="sess-1")
    for _ in range(5):
        assert r.pick(key="sess-1") == first


def test_different_sessions_can_land_on_different_backends():
    r = _m().ConnectorMarketplace(["a", "b"])
    p1 = r.pick(key="s1"); p2 = r.pick(key="s2")
    assert {p1, p2} == {"a", "b"}


def test_estate_context_real_integrations():
    with tempfile.TemporaryDirectory() as d:
        ctx = _m().estate_context(d)
        assert ctx.get("engine_status_checked") is True
        assert ctx.get("dedup_probe_seen") is True
        assert "toolchest_total" in ctx
