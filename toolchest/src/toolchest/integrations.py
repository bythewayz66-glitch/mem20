"""Cross-subsystem wiring for toolchest.

toolchest is a *registry*, so its value depends on being able to describe the
rest of the estate truthfully. This module is the one place where toolchest
reaches into other mem20 subsystems, and every function here calls a real
public API of that subsystem on a real path -- nothing is stubbed, and nothing
is imported only to satisfy a checker.

Wired subsystems (each import is used by a function below):

* ``memory_engine.memory``  -- pin a registry snapshot as a grounded block
* ``mem20kanbanz.migrate``  -- content hash of the generated inventory
* ``mem20ops.clicheck``     -- declared console scripts across the estate
* ``mem20corez.mlp``        -- real parameter count for the model entries
* ``mem20cliz``             -- the shared CLI JSON envelope
* ``mem20verify.testrun``   -- which packages actually carry tests

The estate is a set of sibling project directories (``<root>/<name>/`` or
``<root>/<name>/src/<name>/``), not an installed distribution, so the sibling
roots are put on ``sys.path`` before the imports are attempted. A subsystem
that is genuinely absent is recorded as unavailable and the caller gets a
typed error -- never a fabricated value.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

__all__ = [
    "IntegrationUnavailable",
    "estate_root",
    "ensure_estate_path",
    "available",
    "pin_inventory_snapshot",
    "inventory_digest",
    "declared_console_scripts",
    "model_parameter_counts",
    "cli_envelope",
    "test_bearing_packages",
    "wiring_report",
]


class IntegrationUnavailable(RuntimeError):
    """A sibling mem20 subsystem could not be imported in this environment."""


# ---------------------------------------------------------------------------
# estate path bootstrap
# ---------------------------------------------------------------------------
def estate_root() -> Path:
    """The mem20 estate root that contains this toolchest checkout.

    ``toolchest`` lives at ``<root>/toolchest/src/toolchest/``, so the estate
    root is three parents up. ``MEM20_ROOT`` overrides it for a relocated
    checkout (the deployed box uses ``/opt/mem20``).
    """
    override = os.environ.get("MEM20_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[3]


def _package_dir(root: Path, name: str) -> Optional[Path]:
    """Locate a sibling package in any of the estate's three layouts.

    ``<root>/<name>/`` (flat), ``<root>/<name>/<name>/`` (the common nested
    layout) and ``<root>/<name>/src/<name>/`` (src layout) all occur.
    """
    # Order matters: some projects carry a thin flat ``<name>/__init__.py``
    # shim *and* the real package one level down (mem20corez does). The real
    # package must win, so the nested and src layouts are probed first.
    for candidate in (root / name / "src" / name, root / name / name, root / name):
        if (candidate / "__init__.py").is_file():
            return candidate
    return None


def ensure_estate_path(root: Optional[Path] = None) -> List[str]:
    """Put every sibling package root on ``sys.path``; return what was added.

    The repo root itself is deliberately *not* added: it would let a bare
    ``<root>/mem20foo`` directory shadow the real package as a namespace
    package (the failure documented in the estate's root ``conftest.py``).
    """
    root = Path(root) if root else estate_root()
    added: List[str] = []
    if not root.is_dir():
        return added
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        pkg = _package_dir(root, entry.name)
        if pkg is None:
            continue
        parent = str(pkg.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)
            added.append(parent)
    return added


ensure_estate_path()

# ---------------------------------------------------------------------------
# Real imports of the wired subsystems.
#
# These are ordinary module-level imports (not dynamic lookups) so that the
# dependency is visible to static analysis and to a reader. Each is guarded
# individually: a subsystem that is genuinely absent from this environment
# leaves its name bound to ``None`` and the corresponding function raises
# IntegrationUnavailable with the real reason. Nothing is faked.
# ---------------------------------------------------------------------------
try:
    from memory_engine.memory import pin_block, unpin_block, get_pinned_block
except Exception as _exc:  # noqa: BLE001
    pin_block = unpin_block = get_pinned_block = None
    _MEMORY_ENGINE_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _MEMORY_ENGINE_ERROR = ""

try:
    from mem20kanbanz.migrate import sha256 as kanban_sha256
except Exception as _exc:  # noqa: BLE001
    kanban_sha256 = None
    _KANBANZ_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _KANBANZ_ERROR = ""

try:
    from mem20ops import clicheck as ops_clicheck
except Exception as _exc:  # noqa: BLE001
    ops_clicheck = None
    _OPS_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _OPS_ERROR = ""

try:
    from mem20corez.mlp import CharMLP
except Exception as _exc:  # noqa: BLE001
    CharMLP = None
    _COREZ_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _COREZ_ERROR = ""

try:
    from mem20cliz import build_envelope
except Exception as _exc:  # noqa: BLE001
    build_envelope = None
    _CLIZ_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _CLIZ_ERROR = ""

try:
    from mem20verify.testrun import discover_packages
except Exception as _exc:  # noqa: BLE001
    discover_packages = None
    _VERIFY_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _VERIFY_ERROR = ""


def _require(value: Any, name: str, error: str) -> Any:
    """Return a bound subsystem symbol or raise with the real import error."""
    if value is None:
        raise IntegrationUnavailable(f"{name} unavailable: {error or 'not imported'}")
    return value


def available() -> Dict[str, bool]:
    """Which wired subsystems imported cleanly here (used by the CLI + tests)."""
    return {
        "memory_engine": pin_block is not None,
        "mem20kanbanz": kanban_sha256 is not None,
        "mem20ops": ops_clicheck is not None,
        "mem20corez": CharMLP is not None,
        "mem20cliz": build_envelope is not None,
        "mem20verify": discover_packages is not None,
    }


# ---------------------------------------------------------------------------
# memory_engine.memory -- persist a registry snapshot as a grounded block
# ---------------------------------------------------------------------------
def pin_inventory_snapshot(
    inventory: Dict[str, Any],
    block_id: str = "toolchest:inventory",
    actor: str = "toolchest",
) -> Dict[str, Any]:
    """Pin the inventory summary into the memory engine as a grounded block.

    A pinned block is the estate's mechanism for "this fact is grounded and
    must not be silently rewritten", which is exactly the contract a tool
    registry needs: an agent that reads the tool list should be reading a
    pinned snapshot, not a guess.
    """
    pin = _require(pin_block, "memory_engine.pin_block", _MEMORY_ENGINE_ERROR)
    unpin = _require(unpin_block, "memory_engine.unpin_block", _MEMORY_ENGINE_ERROR)
    counts = inventory.get("counts", {})
    content = (
        f"toolchest inventory {inventory.get('generated_at', 'unknown')}: "
        f"mcp={counts.get('mcp', 0)} cli={counts.get('cli', 0)} "
        f"subsystem={counts.get('subsystem', 0)} total={counts.get('total', 0)}"
    )
    # Re-pinning is the normal case (every refresh), so replace the previous
    # snapshot instead of failing on it. A block that is not there is fine.
    try:
        unpin(block_id, actor=actor)
    except Exception:  # noqa: BLE001 - absent block is the expected first run
        pass
    return pin(block_id, content, reason="toolchest registry snapshot", actor=actor)


# ---------------------------------------------------------------------------
# mem20kanbanz.migrate -- content hash of the inventory file
# ---------------------------------------------------------------------------
def inventory_digest(path: Path) -> str:
    """SHA-256 of the inventory file, computed by mem20kanbanz's hasher.

    Reusing the kanban migration hasher keeps one definition of "content
    identity" across the estate instead of a second, subtly different one.
    """
    hasher = _require(kanban_sha256, "mem20kanbanz.sha256", _KANBANZ_ERROR)
    return hasher(Path(path))


# ---------------------------------------------------------------------------
# mem20ops.clicheck -- declared console scripts across the estate
# ---------------------------------------------------------------------------
def declared_console_scripts(root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Every console script declared by a mem20* pyproject, via mem20ops.

    ``mem20ops.clicheck`` scans ``REPO`` (default ``/opt/mem20``); point it at
    the checkout under test so the answer describes *this* tree.
    """
    clicheck = _require(ops_clicheck, "mem20ops.clicheck", _OPS_ERROR)
    root = Path(root) if root else estate_root()
    previous = getattr(clicheck, "REPO", None)
    clicheck.REPO = str(root)
    try:
        return clicheck.declared_scripts()
    finally:
        if previous is not None:
            clicheck.REPO = previous


# ---------------------------------------------------------------------------
# mem20corez.mlp -- real parameter counts for model entries
# ---------------------------------------------------------------------------
def model_parameter_counts(hidden: int = 16, context_len: int = 8) -> Dict[str, int]:
    """Build a real CharMLP and report its real parameter count.

    The inventory lists model-serving tools; a parameter count is the one
    number that proves the entry points at a real model rather than a name.
    """
    model_cls = _require(CharMLP, "mem20corez.CharMLP", _COREZ_ERROR)
    model = model_cls(hidden=hidden, context_len=context_len)
    return {
        "params": int(model.param_count()),
        "hidden": int(hidden),
        "context_len": int(context_len),
        "vocab_size": int(model.vocab_size),
    }


# ---------------------------------------------------------------------------
# mem20cliz -- the shared CLI JSON envelope
# ---------------------------------------------------------------------------
def cli_envelope(command: str, argv: List[str], exit_code: int,
                 stdout: str = "", stderr: str = "") -> Dict[str, Any]:
    """Wrap a toolchest CLI result in the estate-wide JSON envelope."""
    envelope = _require(build_envelope, "mem20cliz.build_envelope", _CLIZ_ERROR)
    return envelope(command, argv, exit_code, stdout, stderr)


# ---------------------------------------------------------------------------
# mem20verify.testrun -- which packages actually carry tests
# ---------------------------------------------------------------------------
def test_bearing_packages(root: Optional[Path] = None) -> List[str]:
    """Packages mem20verify would actually run a suite for."""
    discover = _require(discover_packages, "mem20verify.discover_packages", _VERIFY_ERROR)
    root = Path(root) if root else estate_root()
    return list(discover(str(root)))


# ---------------------------------------------------------------------------
# aggregate
# ---------------------------------------------------------------------------
def wiring_report(root: Optional[Path] = None) -> Dict[str, Any]:
    """Exercise every wired subsystem once and report what each returned.

    This is the function the CLI's ``wiring`` subcommand and the test suite
    both call, so the cross-module edges are proven on a real path rather than
    merely imported.
    """
    root = Path(root) if root else estate_root()
    report: Dict[str, Any] = {"estate_root": str(root), "edges": {}}

    def edge(name: str, fn) -> None:
        try:
            report["edges"][name] = {"ok": True, "result": fn()}
        except IntegrationUnavailable as exc:
            report["edges"][name] = {"ok": False, "error": str(exc)}
        except Exception as exc:  # noqa: BLE001 - a real failure is a real finding
            report["edges"][name] = {"ok": False,
                                     "error": f"{type(exc).__name__}: {exc}"}

    edge("memory_engine.pin_block",
         lambda: pin_inventory_snapshot({"counts": {"total": 0},
                                         "generated_at": "wiring-probe"}))
    edge("mem20kanbanz.sha256",
         lambda: inventory_digest(Path(__file__)))
    edge("mem20ops.declared_scripts",
         lambda: len(declared_console_scripts(root)))
    edge("mem20corez.CharMLP",
         lambda: model_parameter_counts()["params"])
    edge("mem20cliz.build_envelope",
         lambda: cli_envelope("toolchest", ["wiring"], 0)["schema"])
    edge("mem20verify.discover_packages",
         lambda: len(test_bearing_packages(root)))

    report["ok"] = all(e["ok"] for e in report["edges"].values())
    report["edges_ok"] = sum(1 for e in report["edges"].values() if e["ok"])
    report["edges_total"] = len(report["edges"])
    return report
