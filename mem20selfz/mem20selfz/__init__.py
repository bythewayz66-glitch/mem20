"""mem20 self-healing, self-tuning, forecasting and optimization runtime.

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
    "mem20pipez",
    "mem20pipez",
    "mem20buildsequenceoptimizerz",
    "mem20datalocalityoptimizerz",
    "mem20causalroutingbrainz",
    "mem20milestoneriskpredictorz",
    "mem20qualityriskforecasterz",
    "mem20quantuminspiredoptimizerz",
    "mem20releasereadinesspredictorz",
    "mem20runtimepromptoptimizerz",
    "mem20selfhealingconnectormeshz",
    "mem20selfhealingplansz",
    "mem20selfhealingruntimecivilizationz",
    "mem20selfoptimizingkernelz",
    "mem20selfrepairingtestfactoryz",
    "mem20selftuningresourcegovernorz",
)
__all__ = ["__version__", "MEMBERS"]
