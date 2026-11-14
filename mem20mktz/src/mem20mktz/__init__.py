"""mem20mktz — mem30 Phase 2 marketplace organs on the estate.

Two marketplaces trade real offers (release gate):
  - Inference Marketplace (RM-070) on the Adaptive Inference Scheduler
  - Capability Marketplace (RM-010) on top of the Universal Capability Graph
Plus service bundling (RM-087), adaptive pricing (RM-015), and braid-journaled
resource trades (RM-012) so a composed, priced offer can actually be bought
and the trade becomes a braid node (exit test).
"""
__version__ = "0.1.0"

from .descriptor import (
    MKTZ_DESCRIPTORS,
    all_descriptors,
)
from .service import MarketService

__all__ = ["MKTZ_DESCRIPTORS", "MarketService", "__version__", "all_descriptors"]

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
