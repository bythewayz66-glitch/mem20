"""Cross-subsystem wiring for mem20ops.

mem20ops is the operator's console: it answers "what is actually running, what
is actually declared, and what did the last check actually say". Those answers
live in other subsystems, so this module is where mem20ops reaches out. Every
function calls a real public API on a real path.

Wired subsystems (each import is used by a function below):

* ``toolchest.catalog``     -- the registry: what the box claims to offer
* ``memory_engine.memory``  -- pin an operational snapshot as a grounded block
* ``mem20kanbanz.migrate``  -- content hash of an ops report
* ``mem20corez.mlp``        -- a real model to health-check
* ``mem20cliz``             -- the shared CLI JSON envelope
* ``mem20verify.testrun``   -- which packages actually carry a suite

The estate is a set of sibling project directories, not an installed
distribution, so the sibling roots are put on ``sys.path`` only long enough to
bind the imports below, then removed again -- importing this module must not
change the meaning of any other test's environment probe.

A subsystem that is genuinely absent leaves its symbol bound to ``None`` and
the caller gets a typed error -- never a fabricated value.
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
    "registry_summary",
    "pin_ops_snapshot",
    "report_digest",
    "model_health",
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
    """The mem20 estate root containing this mem20ops checkout.

    ``mem20ops`` lives at ``<root>/mem20ops/src/mem20ops/``, so the estate root
    is three parents up. ``MEM20_ROOT`` overrides it (the deployed box uses
    ``/opt/mem20``).
    """
    override = os.environ.get("MEM20_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[3]


def _package_dir(root: Path, name: str) -> Optional[Path]:
    """Locate a sibling package in any of the estate's three layouts.

    The nested and src layouts are probed before the flat one: some projects
    carry a thin flat ``<name>/__init__.py`` shim *and* the real package one
    level down, and the real package must win.
    """
    for candidate in (root / name / "src" / name, root / name / name, root / name):
        if (candidate / "__init__.py").is_file():
            return candidate
    return None


def ensure_estate_path(root: Optional[Path] = None) -> List[str]:
    """Put every sibling package root on ``sys.path``; return what was added.

    The repo root itself is deliberately *not* added: it would let a bare
    ``<root>/mem20foo`` directory shadow the real package as a namespace
    package.
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


_ADDED_PATHS = ensure_estate_path()

# ---------------------------------------------------------------------------
# Real imports of the wired subsystems.
#
# Ordinary module-level imports, so the dependency is visible to static
# analysis and to a reader. Each is guarded individually: an absent subsystem
# leaves its name bound to ``None`` and the function raises
# IntegrationUnavailable with the real reason. Nothing is faked.
# ---------------------------------------------------------------------------
try:
    from toolchest import catalog as toolchest_catalog
except Exception as _exc:  # noqa: BLE001
    toolchest_catalog = None
    _TOOLCHEST_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _TOOLCHEST_ERROR = ""

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


# The imports above are bound; the estate paths have done their job. Remove
# them again so this module leaves the process exactly as it found it.
for _path in _ADDED_PATHS:
    while _path in sys.path:
        sys.path.remove(_path)
del _path


def _require(value: Any, name: str, error: str) -> Any:
    """Return a bound subsystem symbol or raise with the real import error."""
    if value is None:
        raise IntegrationUnavailable(f"{name} unavailable: {error or 'not imported'}")
    return value


def available() -> Dict[str, bool]:
    """Which wired subsystems imported cleanly here (used by the CLI + tests)."""
    return {
        "toolchest": toolchest_catalog is not None,
        "memory_engine": pin_block is not None,
        "mem20kanbanz": kanban_sha256 is not None,
        "mem20corez": CharMLP is not None,
        "mem20cliz": build_envelope is not None,
        "mem20verify": discover_packages is not None,
    }


# ---------------------------------------------------------------------------
# toolchest.catalog -- what the box claims to offer
# ---------------------------------------------------------------------------
def registry_summary(root: Optional[Path] = None) -> Dict[str, Any]:
    """The registry's counts and generation time, read from the real inventory.

    An operator needs to know whether the tool list they are looking at is
    current. The generation timestamp is the answer, and it only exists if the
    inventory was really built.
    """
    catalog = _require(toolchest_catalog, "toolchest.catalog", _TOOLCHEST_ERROR)
    root = Path(root) if root else estate_root()
    path = root / "toolchest" / "inventory.json"
    if not path.is_file():
        raise IntegrationUnavailable(f"toolchest inventory not found at {path}")
    inventory = catalog.load_inventory(path)
    return {
        "generated_at": inventory.get("generated_at"),
        "counts": dict(inventory.get("counts", {})),
        "entries": len(inventory.get("entries", [])),
    }


# ---------------------------------------------------------------------------
# memory_engine.memory -- pin an operational snapshot
# ---------------------------------------------------------------------------
def pin_ops_snapshot(
    snapshot: Dict[str, Any],
    block_id: str = "mem20ops:snapshot",
    actor: str = "mem20ops",
) -> Dict[str, Any]:
    """Pin an operational snapshot as a grounded block.

    An ops reading that only exists in a terminal is a reading nobody can
    compare against tomorrow. Pinning makes it a durable, grounded surface.
    """
    pin = _require(pin_block, "memory_engine.pin_block", _MEMORY_ENGINE_ERROR)
    unpin = _require(unpin_block, "memory_engine.unpin_block", _MEMORY_ENGINE_ERROR)
    rendered = ", ".join(f"{k}={v}" for k, v in sorted(snapshot.items()))
    content = f"mem20ops snapshot: {rendered}"
    try:
        unpin(block_id, actor=actor)
    except Exception:  # noqa: BLE001 - absent block is the expected first run
        pass
    return pin(block_id, content, reason="mem20ops operational snapshot", actor=actor)


# ---------------------------------------------------------------------------
# mem20kanbanz.migrate -- content hash of an ops report
# ---------------------------------------------------------------------------
def report_digest(path: Path) -> str:
    """SHA-256 of an ops report, computed by mem20kanbanz's hasher.

    Reusing the kanban hasher keeps one definition of content identity across
    the estate instead of a second, subtly different one.
    """
    hasher = _require(kanban_sha256, "mem20kanbanz.sha256", _KANBANZ_ERROR)
    return hasher(Path(path))


# ---------------------------------------------------------------------------
# mem20corez.mlp -- a real model to health-check
# ---------------------------------------------------------------------------
def model_health(hidden: int = 8, context_len: int = 4) -> Dict[str, Any]:
    """Build and exercise a real model, returning what it actually did.

    "Is the box healthy" is not answerable from process liveness alone: a
    running process with a broken tensor engine is down. This runs a real
    forward pass so that failure mode is visible.
    """
    model_cls = _require(CharMLP, "mem20corez.CharMLP", _COREZ_ERROR)
    model = model_cls(hidden=hidden, context_len=context_len)
    completion = model.generate("mem20", n_tokens=4)
    return {
        "params": int(model.param_count()),
        "accuracy": round(float(model.accuracy("mem20ops health check")), 6),
        "completion_len": len(completion),
        "generated": completion != "",
    }


# ---------------------------------------------------------------------------
# mem20cliz -- the shared CLI JSON envelope
# ---------------------------------------------------------------------------
def cli_envelope(command: str, argv: List[str], exit_code: int,
                 stdout: str = "", stderr: str = "") -> Dict[str, Any]:
    """Wrap a mem20ops CLI result in the estate-wide JSON envelope."""
    envelope = _require(build_envelope, "mem20cliz.build_envelope", _CLIZ_ERROR)
    return envelope(command, argv, exit_code, stdout, stderr)


# ---------------------------------------------------------------------------
# mem20verify.testrun -- which packages actually carry a suite
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

    This is what the CLI's ``wiring`` subcommand and the test suite both call,
    so the cross-module edges are proven on a real path rather than merely
    imported.
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

    edge("toolchest.catalog",
         lambda: registry_summary(root)["entries"])
    edge("memory_engine.pin_block",
         lambda: pin_ops_snapshot({"healthy": True})["pinned"])
    edge("mem20kanbanz.sha256",
         lambda: report_digest(Path(__file__)))
    edge("mem20corez.CharMLP",
         lambda: model_health()["params"])
    edge("mem20cliz.build_envelope",
         lambda: cli_envelope("mem20ops", ["wiring"], 0)["schema"])
    edge("mem20verify.discover_packages",
         lambda: len(test_bearing_packages(root)))

    report["ok"] = all(e["ok"] for e in report["edges"].values())
    report["edges_ok"] = sum(1 for e in report["edges"].values() if e["ok"])
    report["edges_total"] = len(report["edges"])
    return report
