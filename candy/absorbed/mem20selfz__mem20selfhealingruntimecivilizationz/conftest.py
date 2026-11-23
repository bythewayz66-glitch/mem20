"""Package-local conftest: bind the real package before pytest walks the tree.

Why this exists
---------------
The estate layout is ``<repo>/<project>/<package>/``, so the *outer* project
directory ``<repo>/mem20selfhealingruntimecivilizationz`` has no ``__init__.py``.
During pytest's collection walk that directory lands on ``sys.path``, Python then
matches its child ``mem20selfhealingruntimecivilizationz/`` as a *namespace
package* (``__file__ = None``), and the name is cached — after which
``import mem20selfhealingruntimecivilizationz.domain`` fails with
``ModuleNotFoundError`` because the namespace portion has no ``domain`` module.

The repository root ``conftest.py`` solves this for the estate as a whole by
pre-importing each package. This file does the same for this package from inside
it, so the suite is also correct when run directly::

    python3 -m pytest mem20selfhealingruntimecivilizationz -q

It is a no-op when the real package is already bound (i.e. under the estate's own
runner), and it never edits ``sys.path`` for anything outside this package.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

PKG = "mem20selfhealingruntimecivilizationz"
_HERE = Path(__file__).resolve().parent          # <repo>/<project>
_PKG_DIR = _HERE / PKG                          # <repo>/<project>/<package>


def _bind_real_package() -> None:
    """Put the project root on sys.path and import the real package now."""
    current = sys.modules.get(PKG)
    if current is not None and getattr(current, "__file__", None) is not None:
        return  # the real package is already bound; nothing to do
    sys.modules.pop(PKG, None)
    parent = str(_HERE)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    if not (_PKG_DIR / "__init__.py").is_file():
        return
    importlib.import_module(PKG)


_bind_real_package()
