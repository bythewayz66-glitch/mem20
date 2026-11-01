"""Cross-subsystem wiring for mem20corez.

mem20corez serves models, so the questions it cannot answer alone are: *which*
model artifact am I serving, is that artifact the one the registry says it is,
and is the result of serving it recorded somewhere durable? This module answers
those by calling six other mem20 subsystems on a real path.

Wired subsystems (each import is used by a function below):

* ``toolchest.catalog``     -- the tool registry: which model-serving tools exist
* ``memory_engine.memory``  -- pin an evaluation result as a grounded block
* ``mem20kanbanz.migrate``  -- content hash of a model artifact
* ``mem20ops.clicheck``     -- declared console scripts across the estate
* ``mem20cliz``             -- the shared CLI JSON envelope
* ``mem20verify.testrun``   -- which packages actually carry tests

The estate is a set of sibling project directories, not an installed
distribution, so the sibling roots are put on ``sys.path`` before the imports
are attempted. A subsystem that is genuinely absent leaves its symbol bound to
``None`` and the caller gets a typed error -- never a fabricated value.
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
    "model_serving_tools",
    "artifact_digest",
    "pin_evaluation",
    "declared_console_scripts",
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
    """The mem20 estate root containing this mem20corez checkout.

    ``mem20corez`` lives at ``<root>/mem20corez/mem20corez/``, so the estate
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


ensure_estate_path()

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
        "toolchest": toolchest_catalog is not None,
        "memory_engine": pin_block is not None,
        "mem20kanbanz": kanban_sha256 is not None,
        "mem20ops": ops_clicheck is not None,
        "mem20cliz": build_envelope is not None,
        "mem20verify": discover_packages is not None,
    }


# ---------------------------------------------------------------------------
# toolchest.catalog -- which model-serving tools the registry knows about
# ---------------------------------------------------------------------------
def model_serving_tools(root: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Model-serving entries from the tool registry, read from the real inventory.

    corez serves models; the registry is the estate's answer to "what else on
    this box serves models". Reading it (rather than hard-coding a list) means
    a newly installed runner shows up here without a code change.
    """
    catalog = _require(toolchest_catalog, "toolchest.catalog", _TOOLCHEST_ERROR)
    root = Path(root) if root else estate_root()
    path = root / "toolchest" / "inventory.json"
    if not path.is_file():
        raise IntegrationUnavailable(f"toolchest inventory not found at {path}")
    inventory = catalog.load_inventory(path)
    terms = ("model", "llm", "infer", "serve", "ollama", "vllm", "llama")
    hits = []
    for entry in inventory.get("entries", []):
        haystack = " ".join([
            entry.get("name", ""), entry.get("description", ""),
            entry.get("category", ""), entry.get("subcategory", ""),
        ]).lower()
        if any(term in haystack for term in terms):
            hits.append({
                "id": entry["id"],
                "kind": entry["kind"],
                "name": entry["name"],
                "category": entry.get("category", ""),
                "runtime_status": entry.get("runtime_status", ""),
            })
    return hits


# ---------------------------------------------------------------------------
# mem20kanbanz.migrate -- content hash of a model artifact
# ---------------------------------------------------------------------------
def artifact_digest(path: Path) -> str:
    """SHA-256 of a model artifact, computed by mem20kanbanz's hasher.

    A served model is only reproducible if you can name the exact bytes you
    served. Reusing the kanban hasher keeps one definition of content identity
    across the estate.
    """
    hasher = _require(kanban_sha256, "mem20kanbanz.sha256", _KANBANZ_ERROR)
    return hasher(Path(path))


# ---------------------------------------------------------------------------
# memory_engine.memory -- pin an evaluation result
# ---------------------------------------------------------------------------
def pin_evaluation(
    model_name: str,
    metrics: Dict[str, Any],
    block_id: Optional[str] = None,
    actor: str = "mem20corez",
) -> Dict[str, Any]:
    """Pin an evaluation result as a grounded block.

    An accuracy or latency number that only exists in a log is a number nobody
    can audit. Pinning it makes it a grounded retrieval surface that is immune
    to pruning, which is what a model-quality claim needs.
    """
    pin = _require(pin_block, "memory_engine.pin_block", _MEMORY_ENGINE_ERROR)
    unpin = _require(unpin_block, "memory_engine.unpin_block", _MEMORY_ENGINE_ERROR)
    block_id = block_id or f"mem20corez:eval:{model_name}"
    rendered = ", ".join(f"{k}={v}" for k, v in sorted(metrics.items()))
    content = f"mem20corez evaluation of {model_name}: {rendered}"
    try:
        unpin(block_id, actor=actor)
    except Exception:  # noqa: BLE001 - absent block is the expected first run
        pass
    return pin(block_id, content, reason="mem20corez evaluation result", actor=actor)


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
# mem20cliz -- the shared CLI JSON envelope
# ---------------------------------------------------------------------------
def cli_envelope(command: str, argv: List[str], exit_code: int,
                 stdout: str = "", stderr: str = "") -> Dict[str, Any]:
    """Wrap a mem20corez CLI result in the estate-wide JSON envelope."""
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
         lambda: len(model_serving_tools(root)))
    edge("memory_engine.pin_block",
         lambda: pin_evaluation("wiring-probe", {"accuracy": 0.0})["pinned"])
    edge("mem20kanbanz.sha256",
         lambda: artifact_digest(Path(__file__)))
    edge("mem20ops.declared_scripts",
         lambda: len(declared_console_scripts(root)))
    edge("mem20cliz.build_envelope",
         lambda: cli_envelope("mem20corez", ["wiring"], 0)["schema"])
    edge("mem20verify.discover_packages",
         lambda: len(test_bearing_packages(root)))

    report["ok"] = all(e["ok"] for e in report["edges"].values())
    report["edges_ok"] = sum(1 for e in report["edges"].values() if e["ok"])
    report["edges_total"] = len(report["edges"])
    return report
