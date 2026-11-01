"""Import-path bootstrap for the braid Python bridge.

Several mem20 subsystems are not installed as distributions in a source
checkout (``toolchest``, ``mem20verify`` and ``mem20ops`` use a ``src/``
layout), so the bridge resolves them relative to the repository root instead of
assuming a site-packages install.

Nothing here mutates global state beyond ``sys.path``; it is idempotent.
"""
from __future__ import annotations

import os
import sys

# braid/py/braid_py/_bootstrap.py -> braid/py/braid_py -> braid/py -> braid -> <repo>
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

_SOURCE_PATHS = (
    REPO_ROOT,
    os.path.join(REPO_ROOT, "mem20core"),
    os.path.join(REPO_ROOT, "toolchest", "src"),
    os.path.join(REPO_ROOT, "mem20verify"),
    os.path.join(REPO_ROOT, "mem20ops", "src"),
)


def ensure_paths() -> str:
    """Put every source-layout package root on ``sys.path``. Returns the root."""
    for path in _SOURCE_PATHS:
        if path not in sys.path:
            sys.path.insert(0, path)
    return REPO_ROOT
