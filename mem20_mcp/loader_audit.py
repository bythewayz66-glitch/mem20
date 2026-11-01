"""Loader-integrity audit for the mem20_mcp forwarding package.

``mem20_mcp`` is not a server. It is a loader: every module in it re-exports the
canonical module of the same name from the running tree at ``/opt/mem20/mcp``,
so the package boots the real tool set instead of a stale copy. That design has
one failure mode that matters, and it is silent:

    a shim that stops forwarding and starts *containing* code.

A shim that has quietly grown its own implementation still imports, still
exposes the right names, and still passes a smoke test -- while the estate now
has two implementations of the same tool and the one on the dispatch path is
whichever the import order happened to pick. The original bug in this package
was exactly that shape: a stale ``tools/world_tools.py`` that had lost
``WorldToolsMixin``, so ``server.py`` raised ``ImportError`` at boot.

So the audit asks the estate's own modules, rather than re-deriving the rules:

``mem20verify.linters.noop_bodies``
    Is a shim's body real forwarding, or a ``pass`` that pretends to be one?

``mem20ops.clicheck.classify_naming``
    Is the *package* named like an estate module, or has something foreign
    appeared? The naming rule is about the estate-facing name, so it is applied
    to the package (``mem20_mcp``), not to each internal module stem -- a shim
    called ``health.py`` is a file inside an estate package, not a foreign tool.

``mem20liez.gates.check_prohibited_uses``
    A loader is a privileged position -- it decides what code the server runs.
    The estate's prohibited-use list applies to it too.

``mem20temporaldatabasefabricz.temporal.interval.contains``
    An audit is a statement about an instant. Half-open interval algebra is the
    estate's one convention for that, and re-deriving it here is the off-by-one
    bug it exists to prevent.

``mem20ircz.filter.classify``
    The server's log is mostly protocol chatter. The audit reports how much of
    it was noise, as evidence rather than a claim.

``mem20dreamz.ledger.commit_raw``
    The audit result is recorded as a content-addressed provenance node, and
    reports honestly when braid is unreachable.

Nothing here imports the MCP SDK, so the audit runs in a bare clone.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

# The estate uses two layouts: ``mem20ops`` and ``mem20temporaldatabasefabricz``
# are src-layout (``<project>/src/<package>/``); the rest are flat
# (``<project>/<package>/``). None is installed in a bare clone, so the project
# roots go on sys.path here and the packages are imported by their real names.
# That keeps the import identical whether the caller is pytest, the CLI, or a
# plain ``python3`` from the repo root -- and it keeps the AST import names the
# conformance gate counts.
_REPO_ROOT = Path(__file__).resolve().parents[1]
for _project in (
    "mem20ops",
    "mem20verify",
    "mem20liez",
    "mem20ircz",
    "mem20temporaldatabasefabricz",
    "mem20dreamz",
):
    for _candidate in (_REPO_ROOT / _project / "src", _REPO_ROOT / _project):
        if _candidate.is_dir() and str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))

from mem20liez.gates import GateError, check_prohibited_uses
from mem20ops.clicheck import classify_naming
from mem20verify.linters import noop_bodies
from mem20ircz.filter import NoiseMeter, classify as classify_wire_line
from mem20temporaldatabasefabricz.temporal.interval import (
    contains as interval_contains,
)
from mem20dreamz import ledger as dreamz_ledger

#: The estate-facing name of this package. The naming rule applies here.
PACKAGE_NAME = "mem20_mcp"

#: A package is an estate module, so it must carry an estate name.
ACCEPTED_NAMINGS = frozenset({"mem20-native", "fs-standard"})

#: Modules that are the loader machinery itself, not shims of a canonical file.
LOADER_MODULES = frozenset({"__init__.py", "_forward.py", "loader_audit.py", "cli.py"})

#: The call every forwarding shim makes.
FORWARD_CALL = "_load"


class AuditRefused(RuntimeError):
    """The audit itself was refused before it could run.

    Carries the check that refused it, so a caller can tell a policy refusal
    apart from an audit that ran and found problems.
    """

    def __init__(self, check: str, reason: str) -> None:
        super().__init__(f"{check}: {reason}")
        self.check = check
        self.reason = reason

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "check": self.check, "reason": self.reason}


@dataclass(frozen=True)
class WireLine:
    """One log line, in the shape ``mem20ircz.filter`` expects.

    The filter is duck-typed against ``mem20botz.irc.Message``. Importing that
    class would drag in the whole bot package just to hand the filter four
    attributes, so the four attributes are carried here instead. The filter's
    contract is the attributes, not the class.
    """

    command: str
    text: str = ""
    prefix: str = ""
    params: tuple[str, ...] = ()

    @property
    def target(self) -> str:
        return self.params[0] if self.params else ""

    @property
    def is_channel(self) -> bool:
        target = self.target
        return bool(target) and target[0] in "#&+!"


@dataclass
class ShimReport:
    """What the audit found about one shim module."""

    module: str
    forwards: bool = False
    via: str = ""
    stub_issues: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.forwards and not self.problems

    def as_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "forwards": self.forwards,
            "via": self.via,
            "stub_issues": self.stub_issues,
            "problems": list(self.problems),
            "ok": self.ok,
        }


@dataclass
class Audit:
    """The result of auditing the whole package."""

    root: str
    package: str = PACKAGE_NAME
    naming: str = ""
    shims: list[ShimReport] = field(default_factory=list)
    wire_kept: int = 0
    wire_swallowed: int = 0
    wire_waste_ratio: float = 0.0
    wire_reasons: dict[str, int] = field(default_factory=dict)
    window_ok: bool = True
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def clean(self) -> bool:
        return all(s.ok for s in self.shims)

    @property
    def broken(self) -> list[ShimReport]:
        return [s for s in self.shims if not s.ok]

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "package": self.package,
            "naming": self.naming,
            "clean": self.clean,
            "shims": [s.as_dict() for s in self.shims],
            "broken": [s.module for s in self.broken],
            "wire_kept": self.wire_kept,
            "wire_swallowed": self.wire_swallowed,
            "wire_waste_ratio": round(self.wire_waste_ratio, 4),
            "wire_reasons": dict(self.wire_reasons),
            "window_ok": self.window_ok,
            "provenance": dict(self.provenance),
        }


# ---------------------------------------------------------------------------
# Individual checks. Each raises AuditRefused; none returns a boolean a caller
# could ignore.
# ---------------------------------------------------------------------------


def check_package_name(package: str = PACKAGE_NAME) -> str:
    """Refuse a package name outside the estate's naming convention.

    Applied to the package, not to each module stem: ``health.py`` inside
    ``mem20_mcp`` is a file in an estate package, not a foreign tool.
    """
    naming = classify_naming(package)
    if naming not in ACCEPTED_NAMINGS:
        raise AuditRefused(
            "naming",
            f"package {package!r} classifies as {naming!r}; an estate package "
            f"must be mem20-native or fs-standard",
        )
    return naming


def check_intended_uses(intended_uses: Iterable[str] | None) -> tuple[str, ...]:
    """Refuse an audit whose declared intended use is prohibited.

    Delegated to ``mem20liez.gates``: the prohibited-use list is the estate's
    ruling, and a second copy of it here would drift.
    """
    uses = tuple(intended_uses or ())
    try:
        check_prohibited_uses(list(uses) if uses else None)
    except GateError as exc:
        raise AuditRefused("prohibited_use", str(exc)) from exc
    return uses


def check_audit_window(valid_from: str | None, valid_to: str | None, at: str | None) -> bool:
    """Refuse an instant outside the declared audit window.

    An absent window is an open interval, which ``contains`` already handles.
    """
    if at is None:
        return True
    if not interval_contains(valid_from, valid_to, at):
        raise AuditRefused(
            "outside_window",
            f"{at} is outside the audit window [{valid_from}, {valid_to})",
        )
    return True


def _forwarding_route(tree: ast.AST, shim_stems: set[str]) -> str:
    """How does this module reach the canonical tree? Empty string if it does not.

    Two legitimate routes exist in this package:

    ``_load(...)``
        The direct route: the shim calls the forwarder itself.

    ``from <sibling> import ...``
        The entry-point route: ``mcp_server.py`` imports ``main`` from the
        ``server`` shim, which is itself a forwarder. That is still forwarding --
        the code that runs is the canonical code -- so it is accepted, but only
        when the sibling is a shim in this package. Importing from anywhere else
        is not forwarding.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == FORWARD_CALL:
                return FORWARD_CALL
            if isinstance(func, ast.Attribute) and func.attr == FORWARD_CALL:
                return FORWARD_CALL
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if node.module in shim_stems:
                return f"from {node.module} import"
    return ""


def audit_shim(path: Path, shim_stems: set[str] | None = None) -> ShimReport:
    """Audit one shim module: does it forward, and is its body real?"""
    report = ShimReport(module=path.name)
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        report.problems.append(f"unreadable: {exc}")
        return report

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        report.problems.append(f"does not parse: {exc.msg} (line {exc.lineno})")
        return report

    stems = shim_stems if shim_stems is not None else {path.stem}

    # Forwarding: the shim must reach the canonical tree, directly or through a
    # sibling shim. A module that defines its own implementation and reaches
    # neither is the silent-drift failure this audit exists to catch.
    report.via = _forwarding_route(tree, stems)
    report.forwards = bool(report.via)
    if not report.forwards:
        report.problems.append(
            f"reaches neither {FORWARD_CALL}() nor a sibling shim; this module "
            f"contains code instead of forwarding to the canonical tree"
        )

    # Stub bodies: a shim whose body is only `pass` pretends to forward.
    issues = noop_bodies(str(path), tree)
    report.stub_issues = len(issues)
    if issues:
        first = issues[0]
        report.problems.append(
            f"{len(issues)} stub body/bodies, first at line {first.line}: {first.message}"
        )

    return report


def audit_package(root: Path) -> list[ShimReport]:
    """Audit every shim module in the package, skipping the loader machinery."""
    root = Path(root)
    shim_stems = {
        p.stem for p in root.glob("*.py") if p.name not in LOADER_MODULES
    }
    reports = []
    for path in sorted(root.glob("*.py")):
        if path.name in LOADER_MODULES:
            continue
        reports.append(audit_shim(path, shim_stems))
    return reports


def filter_wire(
    lines: Sequence[Any] | None, my_nicks: Iterable[str] = ()
) -> tuple[list[WireLine], NoiseMeter]:
    """Drop log noise before it reaches the audit, and meter what was dropped."""
    meter = NoiseMeter()
    kept: list[WireLine] = []
    for raw in lines or ():
        line = raw if isinstance(raw, WireLine) else WireLine(**raw)
        if meter.record(classify_wire_line(line, my_nicks)):
            kept.append(line)
    return kept, meter


def record_provenance(root: str, audit: Audit) -> dict[str, Any]:
    """Record the audit as a content-addressed provenance node.

    ``mem20dreamz.ledger`` reports durability honestly: when braid is not
    reachable the node is recorded as NOT committed, with the reason, rather
    than silently skipped.
    """
    return dreamz_ledger.commit_raw(
        "write:loader_audit",
        f"mem20_mcp:{Path(root).name}",
        {
            "root": root,
            "clean": audit.clean,
            "shims": len(audit.shims),
            "broken": [s.module for s in audit.broken],
        },
    )


# ---------------------------------------------------------------------------
# The one entry point the CLI and the tests call.
# ---------------------------------------------------------------------------


def run_audit(
    root: Path | str | None = None,
    *,
    package: str = PACKAGE_NAME,
    intended_uses: Iterable[str] | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
    at: str | None = None,
    wire_lines: Sequence[Any] | None = None,
    my_nicks: Iterable[str] = (),
    record: bool = True,
) -> Audit:
    """Audit the loader package and return the result.

    Raises :class:`AuditRefused` if a policy check refuses the audit itself.
    """
    naming = check_package_name(package)
    check_intended_uses(intended_uses)
    window_ok = check_audit_window(valid_from, valid_to, at)

    package_root = Path(root) if root else Path(__file__).resolve().parent
    audit = Audit(root=str(package_root), package=package, naming=naming)
    audit.shims = audit_package(package_root)
    audit.window_ok = window_ok

    kept, meter = filter_wire(wire_lines, my_nicks)
    report = meter.report()
    audit.wire_kept = len(kept)
    audit.wire_swallowed = report.get("swallowed", 0)
    audit.wire_waste_ratio = meter.waste_ratio
    audit.wire_reasons = dict(report.get("by_reason", {}))

    if record:
        audit.provenance = record_provenance(str(package_root), audit)
    return audit
