"""mem20 adaptive systems runtime.

Consolidates every organ whose package name contained ``adaptive`` into one
product surface. Former top-level directories are removed; members are listed
here and loadable by short id.
"""

from __future__ import annotations

__version__ = "0.1.0"

# short_id -> former package name (and members/ directory name)
MEMBERS: dict[str, str] = {
    "achievement": "mem20adaptiveachievementenginez",
    "dispatch": "mem20adaptivedispatchenginez",
    "forgetting": "mem20adaptiveforgettingenginez",
    "inference": "mem20adaptiveinferencemarketplacez",
    "interface": "mem20adaptiveinterfacecomposerz",
    "personality": "mem20adaptivepersonalityruntimez",
    "pricing": "mem20adaptivepricingbrainz",
}

FORMER_PACKAGES = tuple(MEMBERS.values())


def load_member(short_id: str):
    """Import a member package by short id if still importable on sys.path."""
    if short_id not in MEMBERS:
        raise KeyError(f"unknown adaptive member {short_id!r}; known={sorted(MEMBERS)}")
    name = MEMBERS[short_id]
    return __import__(name)


__all__ = ["__version__", "MEMBERS", "FORMER_PACKAGES", "load_member"]
