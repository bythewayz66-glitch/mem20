"""Import bootstrap: put the estate root on ``sys.path`` before siblings load.

This package wires into five sibling subsystems (``mem20core``, ``memory_engine``,
``mem20kilnz``, ``mem20secretz``, ``toolchest``). In an installed environment
they are ordinary importable packages; in a bare checkout they are sibling
project directories that are not on ``sys.path``. This module makes both work by
appending the estate root derived from this file's location.

It is repo-relative on purpose: a hardcoded host path would break on every other
checkout, and the estate's hygiene gate rejects added absolute host paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["ensure_estate_on_path", "ESTATE_ROOT"]

# <estate>/mem20webgpuz/mem20webgpuz/_bootstrap.py -> <estate>
ESTATE_ROOT = Path(__file__).resolve().parents[2]


def ensure_estate_on_path() -> list[str]:
    """Append the estate root and the src-layout roots; return what was added."""
    added: list[str] = []
    candidates = [ESTATE_ROOT]
    # src-layout siblings (mem20secretz, toolchest) need their own src dir.
    for name in ("mem20secretz", "toolchest"):
        src = ESTATE_ROOT / name / "src"
        if src.is_dir():
            candidates.append(src)
    for path in candidates:
        text = str(path)
        if text not in sys.path:
            sys.path.append(text)
            added.append(text)
    return added


ensure_estate_on_path()
