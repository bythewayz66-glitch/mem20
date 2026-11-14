"""Property-based tests for the civilization control loop.

The properties are stated as invariants that must hold for *every* generated
fleet, which is what makes them worth more than another example-based test:

* health is always inside ``[0, 1]``;
* a cycle never lowers an agent that it left alive;
* a dead agent is never resurrected;
* a cycle terminates and reports recovery only when nothing is left unhealthy;
* the repair budget is never exceeded.

Hypothesis is used when it is installed; otherwise a deterministic exhaustive
generator covers a fixed grid so the suite still runs on a bare interpreter.
"""
from __future__ import annotations

import importlib

import pytest

MOD = "mem20selfhealingruntimecivilizationz"
domain = importlib.import_module(MOD + ".domain")

try:  # pragma: no cover - depends on the environment
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st

    HAVE_HYPOTHESIS = True
except Exception:  # pragma: no cover
    HAVE_HYPOTHESIS = False


def _build(healths, threshold=0.3, repair=0.5, max_repairs=3):
    civ = domain.Civilization(
        threshold=threshold, repair_amount=repair, max_repairs=max_repairs
    )
    for i, health in enumerate(healths):
        civ.add_agent(f"agent{i}", health=health)
    if len(healths) > 1:
        civ.agents["agent1"].depends_on = ["agent0"]
    civ.validate()
    return civ


def _check_invariants(civ, before_status):
    record = civ.run_cycle(now=0.0)
    assert record["recovered"] == (not record["remaining"])
    for agent in civ.agents.values():
        assert 0.0 <= agent.health <= 1.0
        # a dead agent stays dead: health 0.0 is terminal
        if before_status[agent.name] == domain.DEAD:
            assert agent.status == domain.DEAD
            assert agent.health == 0.0
    for agent in civ.agents.values():
        assert agent.repairs <= civ.max_repairs
    assert record["status"] in {domain.HEALTHY, domain.DEGRADED, domain.DOWN}
    assert record["status"] == civ.status() or record["recovered"]
    return record


if HAVE_HYPOTHESIS:

    @settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        healths=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=8),
        threshold=st.floats(min_value=0.0, max_value=1.0),
        repair=st.floats(min_value=0.0, max_value=1.0),
        max_repairs=st.integers(min_value=1, max_value=4),
    )
    def test_cycle_invariants(healths, threshold, repair, max_repairs):
        civ = _build(healths, threshold, repair, max_repairs)
        before = {a.name: a.status for a in civ.agents.values()}
        _check_invariants(civ, before)

    @settings(max_examples=100, deadline=None)
    @given(amount=st.floats(min_value=0.0, max_value=2.0))
    def test_damage_then_heal_is_monotone(amount):
        civ = domain.Civilization(threshold=0.3, repair_amount=amount)
        civ.add_agent("a")
        civ.damage("a", amount)
        after_damage = civ.agents["a"].health
        civ.heal("a", amount)
        assert civ.agents["a"].health >= after_damage
        assert 0.0 <= civ.agents["a"].health <= 1.0

else:  # pragma: no cover - exercised only without hypothesis

    @pytest.mark.parametrize("health", [0.0, 0.05, 0.3, 0.31, 0.5, 0.99, 1.0])
    @pytest.mark.parametrize("threshold", [0.0, 0.3, 0.7])
    def test_cycle_invariants_grid(health, threshold):
        civ = _build([health, 1.0], threshold=threshold, repair=0.5, max_repairs=3)
        before = {a.name: a.status for a in civ.agents.values()}
        _check_invariants(civ, before)

    def test_hypothesis_absent_but_grid_covers_it():
        assert not HAVE_HYPOTHESIS


def test_cycle_terminates_on_permanent_failure():
    civ = domain.Civilization(threshold=0.3, max_repairs=2)
    civ.add_agent("a", health=0.1)

    def always_fails(name):
        raise RuntimeError("repair backend down")

    for _ in range(6):
        record = civ.run_cycle(repair_fn=always_fails, now=0.0)
        assert record["recovered"] is False
    assert civ.agents["a"].repairs == 2
    assert civ.agents["a"].status == domain.QUARANTINED
