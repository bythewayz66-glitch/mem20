"""Unit tests for the domain model (updated for the 4.0 Civilization API)."""
import importlib

MOD = "mem20selfhealingruntimecivilizationz"


def _m():
    return importlib.import_module(MOD + ".domain")


def test_create():
    m = _m()
    r = m.create_civilization(["a", "b"])
    assert len(r.agents) == 2
    assert r.status() == m.HEALTHY


def test_damage():
    m = _m()
    r = m.create_civilization(["a"])
    m.damage(r, "a", 0.5)
    assert r.agents["a"].health == 0.5


def test_heal():
    m = _m()
    r = m.create_civilization(["a"])
    m.damage(r, "a", 0.5)
    m.heal(r, "a", 0.3)
    assert round(r.agents["a"].health, 6) == 0.8


def test_auto():
    m = _m()
    r = m.create_civilization(["a"])
    m.damage(r, "a", 0.9)
    m.auto_heal(r, now=0.0)
    assert r.agents["a"].health >= 0.5


def test_health():
    m = _m()
    r = m.create_civilization(["a"])
    report = m.civ_health(r)
    assert report["alive"] == 1
    assert report["status"] == "healthy"


def test_first_cycle_on_a_healthy_fleet_repairs_nothing():
    m = _m()
    r = m.create_civilization(["a", "b"])
    record = r.run_cycle(now=0.0)
    assert record["quarantined"] == []
    assert record["repaired"] == []
    assert record["recovered"] is True
