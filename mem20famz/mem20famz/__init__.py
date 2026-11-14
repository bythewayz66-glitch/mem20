from .families import (FAMILIES, ASSIGNMENT, NAMES, families, purpose,
                       members, family_of, spec, orphans, unmapped, stats)
__all__ = ["FAMILIES", "ASSIGNMENT", "NAMES", "families", "purpose",
           "members", "family_of", "spec", "orphans", "unmapped", "stats"]


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
