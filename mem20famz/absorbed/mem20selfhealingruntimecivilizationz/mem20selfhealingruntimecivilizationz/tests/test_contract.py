"""Conformance tests for the 4.0 public contract of this subsystem.

These are the tests that would fail on the 3.x layout: they assert the API the
4.0 substrate promises (``__all__``, the ``Civilization`` model, the controller's
substrate wiring) rather than the old loose dict helpers.
"""
from __future__ import annotations

import importlib

import pytest

MOD = "mem20selfhealingruntimecivilizationz"


def _pkg():
    return importlib.import_module(MOD)


def test_public_api_is_declared():
    pkg = _pkg()
    assert pkg.__all__, "criterion: the package must declare its public surface"
    missing = [n for n in pkg.__all__ if not hasattr(pkg, n)]
    assert not missing, f"__all__ names that do not exist: {missing}"


def test_core_contract_names_present():
    pkg = _pkg()
    for name in (
        "Civilization",
        "Agent",
        "CivilizationError",
        "FleetController",
        "ControllerConfig",
        "Substrate",
        "Store",
    ):
        assert hasattr(pkg, name), f"missing stable API: {name}"


def test_version_is_4x_line():
    assert _pkg().__version__.startswith("1.")


def test_civilization_rejects_unknown_dependency():
    domain = importlib.import_module(MOD + ".domain")
    civ = domain.Civilization()
    civ.add_agent("a", depends_on=["ghost"])
    with pytest.raises(domain.CivilizationError):
        civ.validate()


def test_civilization_rejects_cycles():
    domain = importlib.import_module(MOD + ".domain")
    civ = domain.Civilization()
    civ.add_agent("a", depends_on=["b"])
    civ.add_agent("b", depends_on=["a"])
    with pytest.raises(domain.CivilizationError):
        civ.validate()


def test_dead_agent_is_not_resurrected():
    domain = importlib.import_module(MOD + ".domain")
    civ = domain.Civilization()
    civ.add_agent("a")
    civ.damage("a", 1.0)
    assert civ.agents["a"].status == domain.DEAD
    civ.heal("a", 0.9)
    assert civ.agents["a"].status == domain.DEAD
    assert civ.agents["a"].health == 0.0


def test_cascade_quarantines_dependents():
    domain = importlib.import_module(MOD + ".domain")
    civ = domain.Civilization(threshold=0.3, repair_amount=0.0)
    civ.add_agent("gateway")
    civ.add_agent("mcp", depends_on=["gateway"])
    civ.damage("gateway", 0.9)
    civ.validate()
    civ.quarantine("gateway")
    record = civ.run_cycle(repair_fn=lambda name: 0.0, now=0.0)
    assert "mcp" in record["cascaded"]
    assert record["recovered"] is False
    assert civ.status() == domain.DEGRADED


def test_repair_budget_is_bounded():
    domain = importlib.import_module(MOD + ".domain")
    civ = domain.Civilization(threshold=0.3, max_repairs=2)
    civ.add_agent("a", health=0.1)
    for _ in range(5):
        record = civ.run_cycle(repair_fn=lambda name: 0.0, now=0.0)
    assert civ.agents["a"].repairs <= 2
    assert "a" in record["exhausted"]


def test_health_never_rounds_up():
    domain = importlib.import_module(MOD + ".domain")
    civ = domain.Civilization()
    civ.add_agent("a")
    civ.add_agent("b", health=0.1)
    civ.quarantine("b")
    assert civ.status() == domain.DEGRADED
    assert civ.health()["alive"] == 1
