"""Make sibling monorepo packages importable (issues #33 / #34)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for rel in ("mem20ops", "mem20ops/src", "mem20dreamz"):
    p = _ROOT / rel
    if p.is_dir():
        s = str(p if rel.endswith("src") else _ROOT / rel.split("/")[0])
        if s not in sys.path:
            sys.path.insert(0, s)
ops_src = _ROOT / "mem20ops" / "src"
if ops_src.is_dir() and str(ops_src) not in sys.path:
    sys.path.insert(0, str(ops_src))
