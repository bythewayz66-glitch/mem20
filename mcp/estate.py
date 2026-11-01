"""Estate import bootstrap and the verdict types shared by the MCP surface.

Subsystems live in two layouts: ``<name>/<name>/`` (flat) and
``<name>/src/<name>/`` (src-layout). Both are siblings of the ``mcp`` package, so
the roots are derived from this file's location -- repo-relative, never a host
path. That is what lets a clean clone run the surface without an install step.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent


def estate_roots(repo_root: Optional[Path] = None) -> list[str]:
    """Every sibling project root that can contribute an importable package."""
    root = Path(repo_root) if repo_root is not None else _REPO_ROOT
    roots: list[str] = []
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return roots
    for entry in entries:
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        for candidate in (entry, entry / "src"):
            if (candidate / entry.name).is_dir():
                roots.append(str(candidate))
    return roots


def ensure_estate_on_path(repo_root: Optional[Path] = None) -> list[str]:
    """Put every sibling project root on ``sys.path``; return what was added."""
    added: list[str] = []
    for path in estate_roots(repo_root):
        if path not in sys.path:
            sys.path.insert(0, path)
            added.append(path)
    return added


ensure_estate_on_path()


@dataclass(frozen=True)
class Check:
    """One admission check and its verdict."""

    name: str
    ok: bool
    reason: str

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return self.ok


@dataclass(frozen=True)
class Admission:
    """The full verdict for one tool, with every check that produced it."""

    tool: str
    checks: tuple[Check, ...] = field(default_factory=tuple)

    @property
    def admitted(self) -> bool:
        return all(c.ok for c in self.checks)

    @property
    def refusals(self) -> tuple[Check, ...]:
        return tuple(c for c in self.checks if not c.ok)

    def explain(self) -> str:
        if self.admitted:
            return f"{self.tool}: admitted ({len(self.checks)} checks passed)"
        lines = [f"{self.tool}: refused"]
        lines.extend(f"  - {c.name}: {c.reason}" for c in self.refusals)
        return "\n".join(lines)
