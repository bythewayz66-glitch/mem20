"""mem20secretz — secrets governance for the mem20 estate.

Read-only by construction. This package inspects; it never rewrites, moves, or
redacts anything on disk. Redaction is an output-layer concern belonging to the
caller, never to the store.
"""

from .sweep import Finding, SweepResult, sweep, load_store

__all__ = ["Finding", "SweepResult", "sweep", "load_store"]
__version__ = "0.1.0"


def _discover_absorbed_members():
    try:
        from pathlib import Path as _P
        # package at src/mem20mktz -> absorbed at repo_root/mem20mktz/absorbed
        _adir = _P(__file__).resolve().parents[2] / 'absorbed'
        if _adir.is_dir():
            return tuple(sorted(p.name for p in _adir.iterdir() if p.is_dir() and p.name.startswith('mem20') and p.name.endswith('z')))
    except Exception:
        pass
    return ()

MEMBERS = _discover_absorbed_members()
