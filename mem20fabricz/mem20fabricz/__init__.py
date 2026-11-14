"""mem20 integration fabric runtime (assimilated)."""
from __future__ import annotations

__version__ = "0.1.0"

try:
    from .domain import MEMBERS
except Exception:
    MEMBERS = ()

__all__ = ["__version__", "MEMBERS"]
