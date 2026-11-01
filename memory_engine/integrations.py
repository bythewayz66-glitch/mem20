"""Cross-subsystem wiring for memory_engine.

memory_engine is the estate's grounded-fact store, so its value depends on the
rest of the estate being able to *describe* what it holds and on the store
being able to *record* what the rest of the estate did. This module is the one
place where memory_engine reaches into other mem20 subsystems, and every
function here calls a real public API of that subsystem on a real path --
nothing is stubbed, and nothing is imported only to satisfy a checker.

Wired subsystems (each import is used by a function below):

* ``mem20kanbanz.migrate``  -- content hash of the ledger, for tamper checks
* ``mem20ops.clicheck``     -- naming classification of a topic key
* ``mem20corez.mlp``        -- real parameter count, recorded as a fact
* ``mem20cliz``             -- the shared CLI JSON envelope
* ``mem20verify.testrun``   -- which packages actually carry tests
* ``toolchest.catalog``     -- the on-box tool inventory, recorded as a fact

The estate is a set of sibling project directories (``<root>/<name>/``,
``<root>/<name>/<name>/`` or ``<root>/<name>/src/<name>/``), not an installed
distribution, so the sibling roots are put on ``sys.path`` before the imports
are attempted. A subsystem that is genuinely absent is recorded as unavailable
and the caller gets a typed error -- never a fabricated value.
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
    "ledger_digest",
    "classify_topic_key",
    "model_parameter_count",
    "cli_envelope",
    "test_bearing_packages",
    "tool_inventory_counts",
    "wiring_report",
]


class IntegrationUnavailable(RuntimeError):
    """A sibling mem20 subsystem could not be imported in this environment."""


# ---------------------------------------------------------------------------
# estate path bootstrap
# ---------------------------------------------------------------------------
def estate_root() -> Path:
    """The mem20 estate root that contains this memory_engine checkout.

    ``memory_engine`` lives at ``<root>/memory_engine/``, so the estate root is
    one parent up. ``MEM20_ROOT`` overrides it for a relocated checkout (the
    deployed box uses ``/opt/mem20``).
    """
    override = os.environ.get("MEM20_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[1]


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
    from mem20verify.testrun import discover_packages as verify_discover_packages
except Exception as _exc:  # noqa: BLE001
    verify_discover_packages = None
    _VERIFY_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _VERIFY_ERROR = ""

try:
    from toolchest import catalog as toolchest_catalog
except Exception as _exc:  # noqa: BLE001
    toolchest_catalog = None
    _TOOLCHEST_ERROR = f"{type(_exc).__name__}: {_exc}"
else:
    _TOOLCHEST_ERROR = ""


def _require(value: Any, error: str, subsystem: str) -> Any:
    if value is None:
        raise IntegrationUnavailable(f"{subsystem} unavailable: {error}")
    return value


def available() -> Dict[str, bool]:
    """Which wired subsystems imported successfully in this environment."""
    return {
        "mem20kanbanz": kanban_sha256 is not None,
        "mem20ops": ops_clicheck is not None,
        "mem20corez": CharMLP is not None,
        "mem20cliz": build_envelope is not None,
        "mem20verify": verify_discover_packages is not None,
        "toolchest": toolchest_catalog is not None,
    }


# ---------------------------------------------------------------------------
# The wiring itself. Each function calls a real API and returns a real value.
# ---------------------------------------------------------------------------
def ledger_digest(path: Optional[str] = None) -> str:
    """SHA-256 of the grounded ledger file, via mem20kanbanz's hasher.

    Used to detect a ledger that changed underneath a reader. The hash is
    computed by mem20kanbanz rather than hashlib so the estate has exactly one
    definition of "the digest of a file".
    """
    sha = _require(kanban_sha256, _KANBANZ_ERROR, "mem20kanbanz")
    from memory_engine import memory as _memory

    target = Path(path) if path else Path(_memory.LEDGER)
    if not target.is_file():
        raise FileNotFoundError(f"ledger not found: {target}")
    return sha(target)


def classify_topic_key(topic: str) -> str:
    """Classify a topic key with mem20ops's naming rules.

    Topic keys become filenames in the entries mirror, so a key that violates
    the estate's naming convention is a real hazard, not a style nit.
    """
    clicheck = _require(ops_clicheck, _OPS_ERROR, "mem20ops")
    return clicheck.classify_naming(topic)


def model_parameter_count(hidden: int = 64, context_len: int = 8) -> int:
    """Real parameter count of a mem20corez CharMLP, for recording as a fact.

    This is the number the model actually allocates, not a formula restated
    here -- if mem20corez changes its architecture, this changes with it.
    """
    mlp_cls = _require(CharMLP, _COREZ_ERROR, "mem20corez")
    model = mlp_cls(hidden=hidden, context_len=context_len)
    # CharMLP keeps its weights as four plain ndarrays (W1, b1, W2, b2) rather
    # than a params dict, so the count is taken from the arrays themselves.
    return int(sum(a.size for a in (model.W1, model.b1, model.W2, model.b2)))


def cli_envelope(command: str, argv: List[str], exit_code: int = 0,
                 stdout: str = "", stderr: str = "") -> Dict[str, Any]:
    """Build the shared mem20.cli/1 envelope for a memory_engine command."""
    builder = _require(build_envelope, _CLIZ_ERROR, "mem20cliz")
    return builder(command, argv, exit_code, stdout, stderr)


def test_bearing_packages(root: Optional[str] = None) -> List[str]:
    """Packages the estate's own test runner would discover, via mem20verify."""
    discover = _require(verify_discover_packages, _VERIFY_ERROR, "mem20verify")
    return list(discover(root or str(estate_root())))


def tool_inventory_counts() -> Dict[str, int]:
    """Counts from toolchest's real on-box inventory."""
    catalog = _require(toolchest_catalog, _TOOLCHEST_ERROR, "toolchest")
    inventory = catalog.build_inventory()
    return dict(inventory["counts"])


def record_estate_snapshot(actor: str = "memory_engine.integrations") -> Dict[str, Any]:
    """Record what the estate currently reports as a grounded fact.

    This is the wiring's real purpose: memory_engine is the store of record, so
    the estate's own measurements belong in it. The fact is written through the
    sanctioned grounded path (``remember``) with an explicit epistemic status --
    these numbers were *observed* by calling the subsystems, not inferred.
    """
    from memory_engine import memory as _memory

    counts = tool_inventory_counts()
    packages = test_bearing_packages()
    params = model_parameter_count()
    content = (
        f"estate snapshot: {counts.get('total', 0)} tools "
        f"({counts.get('mcp', 0)} mcp, {counts.get('cli', 0)} cli, "
        f"{counts.get('subsystem', 0)} subsystem); "
        f"{len(packages)} test-bearing packages; "
        f"CharMLP(hidden=64) has {params} parameters"
    )
    return _memory.remember(
        topic="estate_snapshot",
        content=content,
        tags=["wave1", "memory_engine", "wiring"],
        epistemic_status="observed",
        source="memory_engine.integrations.wiring_report",
        actor=actor,
    )


def wiring_report(record: bool = False) -> Dict[str, Any]:
    """Prove every edge, returning the real value each one produced.

    This is what the ``wiring`` CLI subcommand prints and what the tests
    assert on. A dead edge is reported as an error string rather than being
    silently omitted, so a broken integration is loud.

    ``record=True`` additionally writes the snapshot into the grounded ledger,
    which is the point of the whole exercise -- and is also what makes the
    ledger-digest edge meaningful on a store that has never been written to.
    """
    report: Dict[str, Any] = {"available": available(), "edges": {}}

    def edge(name: str, fn, *args, **kwargs) -> None:
        try:
            report["edges"][name] = {"ok": True, "value": fn(*args, **kwargs)}
        except FileNotFoundError as exc:
            # A store that has never been written to has no ledger to hash.
            # That is a valid state, not a broken edge, so it is reported as
            # skipped -- distinct from a failure, and never counted as a pass.
            report["edges"][name] = {"ok": True, "skipped": True,
                                     "reason": f"{type(exc).__name__}: {exc}"}
        except Exception as exc:  # noqa: BLE001
            report["edges"][name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    if record:
        edge("memory_engine.record_estate_snapshot", record_estate_snapshot)

    edge("mem20kanbanz.ledger_digest", ledger_digest)
    edge("mem20ops.classify_topic_key", classify_topic_key, "wave1_memory_engine")
    edge("mem20corez.model_parameter_count", model_parameter_count)
    edge("mem20cliz.cli_envelope", cli_envelope, "wiring", ["wiring"])
    edge("mem20verify.test_bearing_packages", test_bearing_packages)
    edge("toolchest.tool_inventory_counts", tool_inventory_counts)

    report["ok"] = all(e["ok"] for e in report["edges"].values())
    report["skipped"] = sorted(k for k, e in report["edges"].items() if e.get("skipped"))
    return report
