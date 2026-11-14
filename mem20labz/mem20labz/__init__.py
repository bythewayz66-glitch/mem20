"""mem20 laboratory runtime.

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

MEMBERS = _discover_absorbed_members()
if not MEMBERS:
    MEMBERS = (
    "mem20autonomoussaleslaboratoryz",
    "mem20labz",
    "mem20twinz",
    "mem20labz",
    "mem20labz",
    "mem20labz",
    "mem20labz",
    "mem20simz",
    "mem20labz",
    "mem20labz",
)
__all__ = ["__version__", "MEMBERS"]
