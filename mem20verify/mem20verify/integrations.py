"""Cross-subsystem wiring for mem20verify.

mem20verify's job is to tell the truth about the estate, so the questions it
cannot answer alone are: what does the registry say *should* be here, what did
the last verification actually conclude, and is that conclusion recorded
somewhere durable? This module answers those by calling six other mem20
subsystems on a real path.

Wired subsystems (each import is used by a function below):

* ``toolchest.catalog``     -- the registry: the claimed state of the estate
* ``memory_engine.memory``  -- pin a verification verdict as a grounded block
* ``mem20kanbanz.migrate``  -- content hash of the verified report
* ``mem20ops.clicheck``     -- declared console scripts across the estate
* ``mem20corez.mlp``        -- a real model to verify against
* ``mem20cliz``             -- the shared CLI JSON envelope

The estate is a set of sibling project directories, not an installed
distribution, so the sibling roots are put on ``sys.path`` before the imports
are attempted. A subsystem that is genuinely absent leaves its symbol bound to
``None`` and the caller gets a typed error -- never a fabricated value.

Deliberately *not* wired: ``mem20verify`` importing itself. The subsystem's own
modules are the caller, not an edge.
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
    "registry_claims",
    "registry_drift",
    "report_digest",
    "pin_verdict",
    "declared_console_scripts",
    "model_smoke_check",
    "cli_envelope",
    "wiring_report",
]


class IntegrationUnavailable(RuntimeError):
    """A sibling mem20 subsystem could not be imported in this environment."""


# ---------------------------------------------------------------------------
# estate path bootstrap
# ---------------------------------------------------------------------------
def estate_root() -> Path:
    """The mem20 estate root containing this mem20verify checkout.

    ``mem20verify`` lives at ``<root>/mem20verify/mem20verify/``, so the estate
    root is three parents up. ``MEM20_ROOT`` overrides it (the deployed box
    uses ``/opt/mem20``).
    """
    override = os.environ.get("MEM20_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2]


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


# The estate path is bootstrapped only long enough to bind the imports below,
# then restored. Importing this module must not permanently mutate
# ``sys.path``: mem20verify's own suite probes the live engine and relies on
# the ambient path to decide whether that engine is reachable, so a lasting
# bootstrap silently changed the meaning of other tests' skips.
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
        "mem20ops": ops_clicheck is not None,
        "mem20corez": CharMLP is not None,
        "mem20cliz": build_envelope is not None,
    }


# ---------------------------------------------------------------------------
# toolchest.catalog -- what the registry claims, and where reality disagrees
# ---------------------------------------------------------------------------
def registry_claims(root: Optional[Path] = None) -> Dict[str, int]:
    """The registry's claimed counts, read from the real inventory."""
    catalog = _require(toolchest_catalog, "toolchest.catalog", _TOOLCHEST_ERROR)
    root = Path(root) if root else estate_root()
    path = root / "toolchest" / "inventory.json"
    if not path.is_file():
        raise IntegrationUnavailable(f"toolchest inventory not found at {path}")
    inventory = catalog.load_inventory(path)
    return dict(inventory.get("counts", {}))


def registry_drift(root: Optional[Path] = None) -> Dict[str, Any]:
    """Compare what the registry claims with what is actually on disk.

    This is the verification question the registry cannot answer about itself:
    a subsystem the inventory lists must still have a package directory, and a
    subsystem directory on disk must be listed. Drift is reported in both
    directions rather than quietly reconciled.
    """
    catalog = _require(toolchest_catalog, "toolchest.catalog", _TOOLCHEST_ERROR)
    root = Path(root) if root else estate_root()
    path = root / "toolchest" / "inventory.json"
    if not path.is_file():
        raise IntegrationUnavailable(f"toolchest inventory not found at {path}")
    inventory = catalog.load_inventory(path)

    claimed = {e["name"] for e in inventory.get("entries", [])
               if e.get("kind") == "subsystem"}
    on_disk = {d.name for d in root.iterdir()
               if d.is_dir() and not d.name.startswith(".")
               and _package_dir(root, d.name) is not None}

    return {
        "claimed": len(claimed),
        "on_disk": len(on_disk),
        "claimed_but_missing": sorted(claimed - on_disk),
        "on_disk_but_unlisted": sorted(on_disk - claimed),
        "in_sync": claimed == on_disk,
    }


# ---------------------------------------------------------------------------
# mem20kanbanz.migrate -- content hash of the verified report
# ---------------------------------------------------------------------------
def report_digest(path: Path) -> str:
    """SHA-256 of a verification report, computed by mem20kanbanz's hasher.

    A verdict is only auditable if you can name the exact report bytes it came
    from. Reusing the kanban hasher keeps one definition of content identity
    across the estate.
    """
    hasher = _require(kanban_sha256, "mem20kanbanz.sha256", _KANBANZ_ERROR)
    return hasher(Path(path))


# ---------------------------------------------------------------------------
# memory_engine.memory -- pin a verification verdict
# ---------------------------------------------------------------------------
def pin_verdict(
    subject: str,
    verdict: Dict[str, Any],
    block_id: Optional[str] = None,
    actor: str = "mem20verify",
) -> Dict[str, Any]:
    """Pin a verification verdict as a grounded block.

    A pass that only exists in a terminal scrollback is a pass nobody can
    audit. Pinning makes the verdict a grounded retrieval surface that is
    immune to pruning, which is what a release gate needs.
    """
    pin = _require(pin_block, "memory_engine.pin_block", _MEMORY_ENGINE_ERROR)
    unpin = _require(unpin_block, "memory_engine.unpin_block", _MEMORY_ENGINE_ERROR)
    block_id = block_id or f"mem20verify:verdict:{subject}"
    rendered = ", ".join(f"{k}={v}" for k, v in sorted(verdict.items()))
    content = f"mem20verify verdict for {subject}: {rendered}"
    try:
        unpin(block_id, actor=actor)
    except Exception:  # noqa: BLE001 - absent block is the expected first run
        pass
    return pin(block_id, content, reason="mem20verify verification verdict", actor=actor)


# ---------------------------------------------------------------------------
# mem20ops.clicheck -- declared console scripts across the estate
# ---------------------------------------------------------------------------
def declared_console_scripts(root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Every console script declared by a mem20* pyproject, via mem20ops."""
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
# mem20corez.mlp -- a real model to verify against
# ---------------------------------------------------------------------------
def model_smoke_check(hidden: int = 8, context_len: int = 4) -> Dict[str, Any]:
    """Build and exercise a real model, returning what it actually did.

    Verifying the estate means verifying the parts that compute. This runs a
    real forward pass and a real accuracy measurement, so a broken tensor
    engine surfaces as a finding rather than as a green tick.
    """
    model_cls = _require(CharMLP, "mem20corez.CharMLP", _COREZ_ERROR)
    model = model_cls(hidden=hidden, context_len=context_len)
    probe = "mem20verify smoke check"
    accuracy = float(model.accuracy(probe))
    completion = model.generate("mem20", n_tokens=4)
    return {
        "params": int(model.param_count()),
        "accuracy": round(accuracy, 6),
        "completion_len": len(completion),
        "generated": completion != "",
    }


# ---------------------------------------------------------------------------
# mem20cliz -- the shared CLI JSON envelope
# ---------------------------------------------------------------------------
def cli_envelope(command: str, argv: List[str], exit_code: int,
                 stdout: str = "", stderr: str = "") -> Dict[str, Any]:
    """Wrap a mem20verify CLI result in the estate-wide JSON envelope."""
    envelope = _require(build_envelope, "mem20cliz.build_envelope", _CLIZ_ERROR)
    return envelope(command, argv, exit_code, stdout, stderr)


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
         lambda: registry_claims(root).get("total"))
    edge("memory_engine.pin_block",
         lambda: pin_verdict("wiring-probe", {"passed": True})["pinned"])
    edge("mem20kanbanz.sha256",
         lambda: report_digest(Path(__file__)))
    edge("mem20ops.declared_scripts",
         lambda: len(declared_console_scripts(root)))
    edge("mem20corez.CharMLP",
         lambda: model_smoke_check()["params"])
    edge("mem20cliz.build_envelope",
         lambda: cli_envelope("mem20verify", ["wiring"], 0)["schema"])

    report["ok"] = all(e["ok"] for e in report["edges"].values())
    report["edges_ok"] = sum(1 for e in report["edges"].values() if e["ok"])
    report["edges_total"] = len(report["edges"])
    return report
