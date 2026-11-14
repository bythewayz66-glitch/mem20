"""mem20 graph systems runtime.

Crew runtime grouping reviewed packages for joint integration under the
package-review rulings. Member systems live in their own directories;
this runtime provides the registry, CLI surface, and shared surface.
"""

from __future__ import annotations

__version__ = "0.2.0"


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
    "mem20capabilitygapmapperz",
    "mem20crossproductloyaltygraphz",
    "mem20deterministicconfigurationgraphz",
    "mem20dynamicskillgraphz",
    "mem20relationshipcontextgraphz",
    "mem20reversibleexecutiongraphz",
    "mem20semanticobjectgraphz",
)
__all__ = ["__version__", "MEMBERS"]

from . import domain, ecosystem  # noqa: E402,F401
__all__ = ["__version__", "MEMBERS", "domain", "ecosystem"]
