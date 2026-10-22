"""mem20 adaptive systems runtime.

Consolidates every organ whose package name contained ``adaptive`` into one
product surface. Member implementations are vendored under ``members/<short>/``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

__version__ = "0.1.0"

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

_MEMBERS_ROOT = Path(__file__).resolve().parent.parent / "members"


def member_path(short_id: str) -> Path:
    if short_id not in MEMBERS:
        raise KeyError(f"unknown adaptive member {short_id!r}; known={sorted(MEMBERS)}")
    return _MEMBERS_ROOT / short_id


def load_member(short_id: str):
    """Load the primary Python package for a vendored member."""
    base = member_path(short_id)
    former = MEMBERS[short_id]
    candidates = [
        base / former / "__init__.py",
        base / "src" / former / "__init__.py",
        base / former / "runtime.py",
        base / former / "core.py",
    ]
    for init in candidates:
        if not init.is_file():
            continue
        if init.name != "__init__.py":
            spec = importlib.util.spec_from_file_location(
                f"mem20adapz.members.{short_id}", init
            )
            mod = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            return mod
        pkg_dir = init.parent
        if str(pkg_dir.parent) not in sys.path:
            sys.path.insert(0, str(pkg_dir.parent))
        return __import__(former)
    raise FileNotFoundError(f"no vendored sources for {short_id} under {base}")


__all__ = ["__version__", "MEMBERS", "FORMER_PACKAGES", "member_path", "load_member"]
