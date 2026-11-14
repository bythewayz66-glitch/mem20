"""mem20pipez — unified pipeline system."""
from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]


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
__all__ = list(__all__) + ["MEMBERS"]
