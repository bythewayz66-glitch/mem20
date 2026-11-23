"""Redirect: mem20predictiverecallenginez is now mem20prez."""
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[3]
_prez = _root / "mem20prez"
if str(_prez) not in sys.path:
    sys.path.insert(0, str(_prez))
from mem20prez.domain import *  # noqa: F401,F403
from mem20prez import domain
__all__ = list(getattr(domain, "__all__", []))
