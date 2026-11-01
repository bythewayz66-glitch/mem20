"""Resolve the mem20 estate onto ``sys.path`` for this subsystem.

The estate is a monorepo of sibling projects, not a single installed
distribution, and it has two layouts that both need handling:

* ``memory_engine/`` and ``gateway/`` are plain directories at the repo root;
* ``mem20verify/``, ``mem20corez/`` and ``mem20ops/`` are
  ``<project>/<package>/`` layouts, and ``toolchest`` is a ``src/`` layout.

The second layout has a trap. ``mem20corez/__init__.py`` exists as a *shim*
(``__version__`` only) next to the real package at
``mem20corez/mem20corez/__init__.py``. Putting the repo root on ``sys.path``
therefore makes ``import mem20corez`` resolve to the shim, which has no
``quantizer`` submodule — the real package is unreachable even though it is
right there. The same shadowing is what the repo's own root ``conftest.py``
fights.

So this module does two things, in this order: it puts the *inner* package
parent on ``sys.path`` ahead of the repo root, and it evicts any shim that was
already imported. It is idempotent and never raises for a missing sibling — the
caller gets an ``ImportError`` at the point of use naming the project, which is
easier to act on than a bare ``ModuleNotFoundError``.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

# <repo>/<project>/<package>/_bootstrap.py -> <repo>
REPO_ROOT = Path(__file__).resolve().parents[2]

# (project, package) pairs whose real package lives one level down.
_NESTED = (
    ("mem20verify", "mem20verify"),
    ("mem20corez", "mem20corez"),
)

# Projects that are a plain directory at the repo root.
_FLAT = ("memory_engine", "gateway")

# src-layout projects: <project>/src/<package>/
_SRC = (
    ("toolchest", "toolchest"),
    ("mem20ops", "mem20ops"),
)


def _inner_parents() -> list[Path]:
    """The directories that must precede the repo root on ``sys.path``."""
    out: list[Path] = []
    for project, package in _NESTED:
        candidate = REPO_ROOT / project / package
        if (candidate / "__init__.py").is_file():
            out.append(candidate.parent)
    for project, package in _SRC:
        candidate = REPO_ROOT / project / "src" / package
        if (candidate / "__init__.py").is_file():
            out.append(candidate.parent)
    return out


def _evict_shadow(package: str) -> bool:
    """Drop an already-imported shim so the real package can be imported.

    A shim is identified by its location: if the imported module's file is the
    outer ``<project>/__init__.py`` rather than the inner package's, it is the
    wrong one. Returns True when something was evicted.
    """
    module = sys.modules.get(package)
    if module is None:
        return False
    file = getattr(module, "__file__", None)
    if not file:
        return False
    real = REPO_ROOT / package / package / "__init__.py"
    if Path(file).resolve() == real.resolve():
        return False
    del sys.modules[package]
    for name in [n for n in sys.modules if n.startswith(package + ".")]:
        del sys.modules[name]
    return True


def ensure_estate_path() -> list[str]:
    """Make every estate project importable, real package first.

    Returns the paths that were newly added, so a caller (or a test) can assert
    the wiring happened instead of assuming it.
    """
    added: list[str] = []

    # Inner package parents go to the FRONT, in reverse so the first listed
    # project ends up first on the path.
    for path in reversed(_inner_parents()):
        text = str(path)
        if text in sys.path:
            sys.path.remove(text)
        else:
            added.append(text)
        sys.path.insert(0, text)

    # The repo root carries memory_engine/ and gateway/; it goes last so it can
    # never shadow an inner package.
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)
        added.append(root)

    for project, package in _NESTED:
        _evict_shadow(package)

    return added


def require(module: str, project: str):
    """Import ``module`` or fail with a message naming the project to install."""
    ensure_estate_path()
    try:
        return importlib.import_module(module)
    except ImportError as exc:  # pragma: no cover - only on a broken checkout
        raise ImportError(
            f"{module} is unavailable; it ships with the mem20 project "
            f"'{project}' at {REPO_ROOT / project}. Install the estate with "
            f"`git clone` + `pip install -r requirements.txt` (mem20 is not on "
            f"PyPI). Original error: {exc}"
        ) from exc


def store_path(default: str | None = None) -> str:
    """The memory-engine store this subsystem should read and write.

    ``MEM20_STORE_PATH`` wins so a caller can point the whole subsystem at an
    isolated store (tests do exactly that); otherwise a per-subsystem directory
    under the user's mem20 store is used.
    """
    env = os.environ.get("MEM20_STORE_PATH")
    if env:
        return env
    if default:
        return default
    return os.path.join(os.path.expanduser("~"), ".mem20", "store")
