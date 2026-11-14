"""mem20 studio runtime.

Crew runtime grouping reviewed packages for joint integration under the
package-review rulings. Member systems live in their own directories;
this runtime provides the registry, CLI surface, and shared surface.
"""

from __future__ import annotations

__version__ = "0.1.0"


def _discover_absorbed_members():
    try:
        from pathlib import Path as _P
        _adir = _P(__file__).resolve().parents[1] / 'absorbed'
        if _adir.is_dir():
            return tuple(sorted(p.name for p in _adir.iterdir() if p.is_dir() and p.name.startswith('mem20') and p.name.endswith('z')))
    except Exception:
        pass
    return ()

_ABSORBED_MEMBERS = _discover_absorbed_members()
_ORIGINAL_MEMBERS = ("mem20studioz",)
_seen = set()
MEMBERS = tuple(m for m in list(_ORIGINAL_MEMBERS) + list(_ABSORBED_MEMBERS) if not (m in _seen or _seen.add(m)))
if len(MEMBERS) <= 1 and _ABSORBED_MEMBERS:
    MEMBERS = tuple(_ABSORBED_MEMBERS)
__all__ = ["__version__", "MEMBERS"]
