"""Redirect: mem20predictiverecallenginez is now mem20prez."""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[3]
_prez = _root / "mem20prez"
if str(_prez) not in sys.path:
    sys.path.insert(0, str(_prez))
try:
    from mem20prez.domain import *  # noqa: F401,F403
    from mem20prez import domain
except ImportError:
    # mem20prez was never created; the local domain.py is the implementation.
    from . import domain  # noqa: F401
    from .domain import *  # noqa: F401,F403
__all__ = list(getattr(domain, "__all__", []))
