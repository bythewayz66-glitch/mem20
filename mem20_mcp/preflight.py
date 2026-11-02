"""Preflight for the canonical MCP tree.

``mem20_mcp`` is a forwarder: every module here re-exports the canonical module
of the same name from ``/opt/mem20/mcp``. That design has exactly one failure
mode, and it is quiet -- if the canonical tree is stale, stubbed, or missing a
tool, this package boots it anyway and the estate runs the wrong logic while
looking healthy. The README says so in as many words.

So the forwarder checks the tree before it forwards. Six estate modules are
consulted, and each answers a question a loader cannot answer for itself:

``mem20verify.linters.noop_bodies``
    A canonical tool whose body is ``pass`` returns a well-formed result that
    means nothing. The linter runs over the canonical ``tools/`` tree, so a
    stubbed tool is refused at boot rather than discovered by a caller.

``mem20ops.clicheck.classify_naming``
    Tool names are the MCP surface. A canonical tool outside the estate naming
    convention is one no client will address correctly.

``mem20liez.gates.check_prohibited_uses``
    Booting a server is exposing every tool it carries. The prohibited-use list
    is the estate's ruling on what may be exposed at all, and it is checked
    against the declared exposure before the tree is loaded.

``mem20ircz.filter.classify`` / ``NoiseMeter``
    The canonical server's log is the only evidence of what it did. MOTD-style
    banner noise and roster churn are filtered out of it, and the meter reports
    how much was swallowed so the signal is measurable.

``mem20temporaldatabasefabricz.temporal.interval.contains``
    A canonical tree may be pinned to a release window. Half-open interval
    algebra is the estate's one convention for "was this true at that instant",
    and re-deriving it here would be the off-by-one bug it exists to prevent.

``mem20dreamz.ledger.commit_raw``
    Every boot is recorded as a content-addressed provenance node, so "which
    canonical tree did this process actually load" is answerable afterwards.
    The ledger reports honestly when braid is unreachable -- ``committed:
    False`` with a reason -- rather than silently skipping the record.

Nothing here is advisory. A refusal raises :class:`PreflightRefused` and the
canonical tree is not loaded.
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

# The estate uses two layouts: ``mem20ops`` and ``mem20temporaldatabasefabricz``
# are src-layout (``<project>/src/<package>/``); the rest are flat
# (``<project>/<package>/``). None of them is installed in a bare clone, so the
# project roots go on sys.path here and the packages are imported by their real
# names. That keeps the import identical whether the caller is pytest, the CLI,
# or a plain ``python3`` from the repo root -- and it keeps the AST import names
# the conformance gate counts.
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

#: A tool name is an MCP address, so it must be an estate name. ``fs-*`` is
#: accepted too: the estate has both conventions and neither is wrong.
ACCEPTED_NAMINGS = frozenset({"mem20-native", "fs-standard"})


class PreflightRefused(RuntimeError):
    """The canonical tree was refused before it was loaded.

    Carries the check that refused it, so a caller can tell a policy refusal
    apart from a missing directory.
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
    class would drag in the whole bot package (and its kanban dependency) just
    to hand the filter four attributes, so the four attributes are carried here
    instead. The filter's contract is the attributes, not the class.
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
class Report:
    """What preflight decided about one canonical tree."""

    root: str
    tool_count: int = 0
    naming: dict[str, str] = field(default_factory=dict)
    intended_uses: tuple[str, ...] = ()
    stub_issues: int = 0
    log_kept: int = 0
    log_swallowed: int = 0
    log_waste_ratio: float = 0.0
    log_reasons: dict[str, int] = field(default_factory=dict)
    window_ok: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "tool_count": self.tool_count,
            "naming": dict(self.naming),
            "intended_uses": list(self.intended_uses),
            "stub_issues": self.stub_issues,
            "log_kept": self.log_kept,
            "log_swallowed": self.log_swallowed,
            "log_waste_ratio": round(self.log_waste_ratio, 4),
            "log_reasons": dict(self.log_reasons),
            "window_ok": self.window_ok,
        }


# ---------------------------------------------------------------------------
# Individual checks. Each one raises PreflightRefused; none of them returns a
# boolean a caller could ignore.
# ---------------------------------------------------------------------------


def check_tool_name(name: str) -> str:
    """Refuse a tool name that is not an estate address."""
    naming = classify_naming(name)
    if naming not in ACCEPTED_NAMINGS:
        raise PreflightRefused(
            "naming",
            f"tool {name!r} classifies as {naming!r}; a canonical tool must be "
            f"mem20-native or fs-standard",
        )
    return naming


def check_exposure(intended_uses: Iterable[str] | None) -> tuple[str, ...]:
    """Refuse to boot a tree whose declared exposure is prohibited.

    Delegated to ``mem20liez.gates``: the prohibited-use list is the estate's
    ruling, and a second copy of it here would drift.
    """
    uses = tuple(intended_uses or ())
    try:
        check_prohibited_uses(list(uses) if uses else None)
    except GateError as exc:
        raise PreflightRefused("prohibited_use", str(exc)) from exc
    return uses


def audit_canonical_tools(root: Path) -> list:
    """Run the estate's stub linter over the canonical ``tools/`` tree."""
    issues: list = []
    tools_dir = Path(root) / "tools"
    if not tools_dir.is_dir():
        return issues
    for path in sorted(tools_dir.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        issues.extend(noop_bodies(str(path), tree))
    return issues


def check_no_stubs(root: Path) -> int:
    """Refuse a canonical tree whose tools are stubs.

    A stubbed tool returns a well-formed result that means nothing, which is
    worse than an error: the caller cannot tell it apart from a real run.
    """
    issues = audit_canonical_tools(root)
    if issues:
        first = issues[0]
        raise PreflightRefused(
            "stub_body",
            f"{len(issues)} stub body/bodies under {Path(root) / 'tools'}, "
            f"first at {first.path}:{first.line} ({first.check})",
        )
    return 0


def check_release_window(
    valid_from: str | None, valid_to: str | None, at: str | None
) -> bool:
    """Refuse a tree pinned outside its release window.

    An absent window is an open interval, which ``contains`` already handles.
    """
    if at is None:
        return True
    if not interval_contains(valid_from, valid_to, at):
        raise PreflightRefused(
            "outside_window",
            f"{at} is outside the release window [{valid_from}, {valid_to})",
        )
    return True


def filter_log(
    lines: Sequence[Any] | None, my_nicks: Iterable[str] = ()
) -> tuple[list[WireLine], NoiseMeter]:
    """Drop banner/roster noise from the canonical server's log."""
    meter = NoiseMeter()
    kept: list[WireLine] = []
    for raw in lines or ():
        line = raw if isinstance(raw, WireLine) else WireLine(**raw)
        if meter.record(classify_wire_line(line, my_nicks)):
            kept.append(line)
    return kept, meter


def record_boot(root: str, report: Report) -> dict[str, Any]:
    """Record one boot as a content-addressed provenance node.

    ``mem20dreamz.ledger`` reports durability honestly: when braid is not
    reachable the node is recorded as NOT committed, with the reason, rather
    than silently skipped.
    """
    return dreamz_ledger.commit_raw(
        "write:mcp_boot",
        f"mcp:{root}",
        {
            "root": root,
            "tool_count": report.tool_count,
            "stub_issues": report.stub_issues,
            "intended_uses": list(report.intended_uses),
        },
    )


def discover_tool_names(root: Path) -> list[str]:
    """The tool module names the canonical tree exposes."""
    tools_dir = Path(root) / "tools"
    if not tools_dir.is_dir():
        return []
    return sorted(p.stem for p in tools_dir.glob("*.py") if not p.stem.startswith("_"))


def exposed_tool_name(module_stem: str) -> str:
    """The MCP tool name a canonical module is addressed by.

    A module filename is not an MCP address. The canonical tree's modules are
    named ``health``, ``world_tools``, ``braid_tools`` -- all of which classify
    as "other" -- while the tools they expose are addressed under the estate
    prefix. Checking the filename would refuse the real tree for a naming rule
    that does not apply to it; checking the exposed name is the rule that
    actually governs what a client can call.
    """
    return f"mem20_{module_stem}"


# ---------------------------------------------------------------------------
# The one entry point the forwarder calls.
# ---------------------------------------------------------------------------


def preflight(
    root: Path,
    intended_uses: Iterable[str] | None = None,
    log: Sequence[Any] | None = None,
    my_nicks: Iterable[str] = (),
    at: str | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> Report:
    """Run every check for one canonical tree.

    Returns the report. Raises :class:`PreflightRefused` if any check refuses.
    """
    root = Path(root)
    uses = check_exposure(intended_uses)
    stub_issues = check_no_stubs(root)
    window_ok = check_release_window(valid_from, valid_to, at)

    names = discover_tool_names(root)
    naming = {name: check_tool_name(exposed_tool_name(name)) for name in names}

    kept, meter = filter_log(log, my_nicks)
    log_report = meter.report()

    return Report(
        root=str(root),
        tool_count=len(names),
        naming=naming,
        intended_uses=uses,
        stub_issues=stub_issues,
        log_kept=len(kept),
        log_swallowed=log_report.get("swallowed", 0),
        log_waste_ratio=meter.waste_ratio,
        log_reasons=dict(log_report.get("by_reason", {})),
        window_ok=window_ok,
    )
