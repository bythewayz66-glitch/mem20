"""Estate path resolution shared by this package's seam modules.

The estate is a set of sibling projects in one checkout, each with its own
layout. Nothing installing them together would be safe (they are not on PyPI),
so the seam puts the right roots on ``sys.path`` before importing anything, and
records which project failed when one does.
"""

from __future__ import annotations

import sys
from pathlib import Path

__all__ = ["REPO_ROOT", "UNAVAILABLE", "estate_path", "require", "need"]

# src/ layout: <repo>/mem20temporaldatabasefabricz/src/<pkg>/temporal/estate.py
REPO_ROOT = Path(__file__).resolve().parents[4]

# Projects laid out as a package directly at the repo root.
_FLAT = ("memory_engine", "gateway", "mem20liez", "mem20ircz", "mem20dreamz",
         "mem20corez", "mem20botz")

# Projects laid out as <project>/<package>/, which needs <project> on the path.
_NESTED = ("mem20verify",)

# Projects laid out as <project>/src/<package>/, which needs <project>/src.
_SRC = ("mem20ops", "mem20secretz", "toolchest")

UNAVAILABLE: dict[str, str] = {}
_PATHS_READY = False


def _add(path: Path) -> None:
    text = str(path)
    if text in sys.path:
        sys.path.remove(text)
    sys.path.insert(0, text)


def estate_path() -> list[str]:
    """Put every estate project root on ``sys.path``, inner package first.

    Returns the paths added, so a test can assert the wiring ran instead of
    trusting it. Idempotent.
    """
    global _PATHS_READY
    if _PATHS_READY:
        return []
    added: list[str] = []
    # src/ and nested layouts go to the FRONT: <project>/src/<pkg>/__init__.py is
    # the real package, and leaving the repo root first would let the outer
    # project directory match as a namespace package (__file__ = None, no
    # attributes) - the shadowing the estate's root conftest.py fights.
    for project in reversed(_SRC):
        candidate = REPO_ROOT / project / "src"
        if candidate.is_dir():
            _add(candidate)
            added.append(str(candidate))
    for project in reversed(_NESTED):
        candidate = REPO_ROOT / project
        if (candidate / project / "__init__.py").is_file():
            _add(candidate)
            added.append(str(candidate))
    for project in reversed(_FLAT):
        candidate = REPO_ROOT / project
        if candidate.is_dir():
            _add(candidate)
            added.append(str(candidate))
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.append(root)
        added.append(root)
    _PATHS_READY = True
    return added


def require(module: str, project: str):
    """Import ``module`` or raise an ImportError naming the project to install."""
    estate_path()
    try:
        return __import__(module, fromlist=["*"])
    except ImportError as exc:  # pragma: no cover - only on a broken checkout
        UNAVAILABLE[module] = f"{type(exc).__name__}: {exc}"
        raise ImportError(
            f"{module} is unavailable; it ships with the mem20 project "
            f"'{project}' at {REPO_ROOT / project}. The estate installs from "
            f"source (mem20 is not on PyPI): git clone + pip install -r "
            f"requirements.txt. Original error: {exc}"
        ) from exc


def need(symbol, name: str, project: str):
    """Return an imported estate symbol, or raise naming the project to install.

    A symbol is ``None`` when its project failed to import at module load; the
    failure is deferred to the call that actually needs it, so a checkout missing
    one unrelated project still loads the rest of the seam.
    """
    if symbol is None:
        raise ImportError(
            f"{name} is unavailable. It ships with the mem20 project '{project}' "
            f"at {REPO_ROOT / project}. (mem20 installs from source, not PyPI.)"
        )
    return symbol


def estate_status() -> dict:
    """One call answering 'is this subsystem's estate reachable?'.

    Reported per project, so a partial checkout is visible as a partial checkout
    rather than as seven unrelated failures. Used by ``doctor`` and stamped into
    exports.
    """
    from . import estate_calls, estate_surface

    symbols = {
        "memory_engine": estate_calls._validate_event_time,
        "mem20verify": estate_calls._integrity_check,
        "mem20ops": estate_calls._identity_check,
        "mem20secretz": estate_calls._classify_secret_value,
        "mem20liez": estate_calls._check_prohibited_uses,
        "mem20ircz": estate_surface._classify_wire_line,
        "toolchest": estate_surface._load_inventory,
    }
    return {
        "repo_root": str(REPO_ROOT),
        "wired": sorted(name for name, sym in symbols.items() if sym is not None),
        "unavailable": dict(UNAVAILABLE),
    }
