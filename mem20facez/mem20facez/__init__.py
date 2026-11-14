"""mem20 interface and workspace runtime. Preserves MEMBERS/__version__/cli.main compatibility."""
from __future__ import annotations
__version__ = "1.0.0"

def _discover_absorbed_members():
    try:
        from pathlib import Path as _P
        _adir = _P(__file__).resolve().parents[1] / 'absorbed'
        if _adir.is_dir():
            return tuple(sorted(p.name for p in _adir.iterdir() if p.is_dir() and p.name.startswith('mem20') and p.name.endswith('z')))
    except Exception:
        pass
    return ()

_ORIGINAL_MEMBERS = (
    "mem20adaptiveinterfacecomposerz","mem20musicvisualsynchronizerz","mem20parallelworkstreamcomposerz",
    "mem20spatialcommanduniversez","mem20spatialexperiencedesignerz","mem20visualagentblackboardz",
    "mem20visualdataflowcomposerz","mem20voicetoactionswitchboardz",
)
_ABSORBED_MEMBERS = _discover_absorbed_members()
_seen = set()
MEMBERS = tuple(m for m in list(_ORIGINAL_MEMBERS) + list(_ABSORBED_MEMBERS) if not (m in _seen or _seen.add(m)))
__all__ = ["__version__", "MEMBERS"]
