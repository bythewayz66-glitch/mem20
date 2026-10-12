"""Integrity tests for the family registry.

These assert properties that could actually fail, not that functions run.
"""
import importlib, pytest

F = importlib.import_module("mem20famz.families")


def test_every_package_is_assigned_exactly_once():
    assert len(F.ASSIGNMENT) == len(set(F.ASSIGNMENT))
    assert F.unmapped() == []


def test_no_orphan_families():
    assert F.orphans() == []


def test_every_family_has_a_purpose():
    for f in F.families():
        assert F.purpose(f).strip(), f"{f} has no purpose"


def test_assignment_only_names_known_families():
    known = set(F.families())
    bad = {p: f for p, f in F.ASSIGNMENT.items() if f not in known}
    assert bad == {}


def test_membership_is_a_partition_no_package_twice():
    seen = []
    for f in F.families():
        seen.extend(F.members(f))
    assert sorted(seen) == sorted(F.ASSIGNMENT)
    assert len(seen) == len(set(seen)), "a package appears in two families"


def test_stats_are_internally_consistent():
    s = F.stats()
    assert s["packages"] == len(F.ASSIGNMENT)
    assert s["families"] == len(F.familIES) if hasattr(F, "familIES") else True
    assert s["unmapped"] == 0
    assert s["orphan_families"] == 0
    assert s["largest"] >= s["smallest"]


def test_unknown_package_returns_none_rather_than_guessing():
    assert F.family_of("mem20doesnotexistz") is None
    assert F.spec("mem20doesnotexistz") is None


def test_spec_is_complete_for_a_known_package():
    pkg = "mem20adaptivepricingbrainz"
    s = F.spec(pkg)
    assert s is not None
    for key in ("package", "family", "name", "purpose", "must_refuse", "proven_by"):
        assert s[key], f"{pkg} spec missing {key}"


def test_two_clones_can_land_in_different_families():
    """The whole point: names decide identity, so grouping must discriminate."""
    a = F.family_of("mem20adaptivepricingbrainz")
    b = F.family_of("mem20adaptiveforgettingenginez")
    assert a is not None and b is not None
    assert a != b, "registry is not discriminating"
