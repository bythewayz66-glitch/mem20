"""mem20 agentz — the agent platform, built directly into mem20.

Full-fidelity cleanroom: every known capability of the absorbed agent platform
re-implemented on mem20 natives under mem20 branding. See docs/PLAN.md for the
feature inventory + architecture map.
"""

__version__ = "0.1.0"
__all__ = ["__version__", "config", "profiles", "sessions"]

from . import config, profiles, sessions  # noqa: F401,E402

def _discover_absorbed_members():
    try:
        from pathlib import Path as _P
        _adir = _P(__file__).resolve().parents[1] / 'absorbed'
        if _adir.is_dir():
            return tuple(sorted(p.name for p in _adir.iterdir() if p.is_dir() and p.name.startswith('mem20') and p.name.endswith('z')))
    except Exception:
        pass
    return ()

ABSORBED_MEMBERS = _discover_absorbed_members()
__all__ = list(__all__) + ["ABSORBED_MEMBERS"]
