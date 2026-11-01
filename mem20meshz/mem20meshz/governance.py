"""Admission control for the mesh runtime.

The six mesh engines under :mod:`mem20meshz.meshes` were vendored from six
separate top-level packages. Each one used to be its own subsystem with its own
policy surface; after consolidation they share one dispatcher, and a shared
dispatcher is exactly where a policy that lived in one of them silently stops
being enforced. This module is that policy, in one place, on the path every
mesh execution takes.

Six estate modules are consulted, and each one answers a question the mesh
runtime cannot answer for itself:

``mem20liez.gates.check_prohibited_uses``
    A crisis-response mesh is the single most dangerous thing in this estate to
    point at a person. The prohibited-use list is the estate's ruling on what
    these engines may never be used for, and it is checked here before any mesh
    sees the request -- not inside the mesh, where a new mesh would have to
    remember to re-implement it.

``mem20ops.clicheck.classify_naming``
    The mesh is exposed as an MCP tool. A request that names a tool outside the
    estate's naming convention is a misroute, and dispatching it would run a
    mesh on behalf of a caller that meant something else.

``mem20verify.linters.noop_bodies``
    A mesh whose engine body is ``pass`` returns a clean-looking result that
    means nothing. The linter is run over the mesh's own source before dispatch,
    so a stubbed mesh is refused rather than trusted.

``mem20ircz.filter.classify`` / ``NoiseMeter``
    Meshes that ingest channel traffic were paying for MOTD bursts and roster
    churn. The wire filter runs before the mesh, and the meter reports what was
    swallowed so the saving is evidence rather than a claim.

``mem20temporaldatabasefabricz.temporal.interval.contains``
    A mesh may declare an operating window. Half-open interval algebra is the
    estate's one convention for "was this true at that instant", and re-deriving
    it here would be the off-by-one bug it exists to prevent.

``mem20dreamz.ledger.commit_raw``
    Every execution is recorded as a content-addressed provenance node. The
    ledger reports honestly when braid is unavailable -- ``committed: False``
    with a reason -- because a lineage that silently stops being
    content-addressed looks identical to one that is.

Nothing here is advisory. A refusal raises :class:`MeshRefused` and the mesh
does not run.
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
_REPO_ROOT = Path(__file__).resolve().parents[2]
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

#: A mesh tool is an estate tool, so it must carry an estate name. ``fs-*`` is
#: accepted too: the estate has both conventions and neither is wrong.
ACCEPTED_NAMINGS = frozenset({"mem20-native", "fs-standard"})

#: Prefix every mesh tool is exposed under.
TOOL_PREFIX = "mem20meshz"


class MeshRefused(RuntimeError):
    """A mesh execution was refused by admission control.

    Carries the check that refused it, so a caller can tell a policy refusal
    apart from a mesh that ran and failed.
    """

    def __init__(self, check: str, reason: str) -> None:
        super().__init__(f"{check}: {reason}")
        self.check = check
        self.reason = reason

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "check": self.check, "reason": self.reason}


@dataclass(frozen=True)
class WireLine:
    """One inbound protocol line, in the shape ``mem20ircz.filter`` expects.

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
class Admission:
    """What admission control decided about one mesh execution."""

    mesh: str
    tool: str
    naming: str = ""
    intended_uses: tuple[str, ...] = ()
    wire_kept: int = 0
    wire_swallowed: int = 0
    wire_waste_ratio: float = 0.0
    wire_reasons: dict[str, int] = field(default_factory=dict)
    stub_issues: int = 0
    window_ok: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "mesh": self.mesh,
            "tool": self.tool,
            "naming": self.naming,
            "intended_uses": list(self.intended_uses),
            "wire_kept": self.wire_kept,
            "wire_swallowed": self.wire_swallowed,
            "wire_waste_ratio": round(self.wire_waste_ratio, 4),
            "wire_reasons": dict(self.wire_reasons),
            "stub_issues": self.stub_issues,
            "window_ok": self.window_ok,
        }


# ---------------------------------------------------------------------------
# Individual checks. Each one raises MeshRefused; none of them returns a
# boolean a caller could ignore.
# ---------------------------------------------------------------------------


def check_tool_name(tool: str) -> str:
    """Refuse a tool name outside the estate's naming convention."""
    naming = classify_naming(tool)
    if naming not in ACCEPTED_NAMINGS:
        raise MeshRefused(
            "naming",
            f"tool {tool!r} classifies as {naming!r}; a mesh tool must be "
            f"mem20-native or fs-standard",
        )
    return naming


def check_intended_uses(intended_uses: Iterable[str] | None) -> tuple[str, ...]:
    """Refuse a request whose declared intended use is prohibited.

    Delegated to ``mem20liez.gates``: the prohibited-use list is the estate's
    ruling, and a second copy of it here would drift.
    """
    uses = tuple(intended_uses or ())
    try:
        check_prohibited_uses(list(uses) if uses else None)
    except GateError as exc:
        raise MeshRefused("prohibited_use", str(exc)) from exc
    return uses


def audit_mesh_source(mesh_dir: Path) -> list:
    """Run the estate's stub linter over one mesh's own source."""
    issues: list = []
    for path in sorted(Path(mesh_dir).rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        issues.extend(noop_bodies(str(path), tree))
    return issues


def check_no_stubs(mesh_dir: Path) -> int:
    """Refuse a mesh whose engine body is a stub.

    A stubbed engine returns a well-formed result that means nothing, which is
    worse than an error: the caller cannot tell it apart from a real run.
    """
    issues = audit_mesh_source(mesh_dir)
    if issues:
        first = issues[0]
        raise MeshRefused(
            "stub_body",
            f"{len(issues)} stub body/bodies in {Path(mesh_dir).name}, "
            f"first at {first.path}:{first.line} ({first.check})",
        )
    return 0


def check_operating_window(config: dict, at: str | None) -> bool:
    """Refuse an instant outside the mesh's declared operating window.

    An absent window is an open interval, which ``contains`` already handles:
    ``contains(None, None, at)`` is true for every instant.
    """
    if at is None:
        return True
    if not interval_contains(config.get("valid_from"), config.get("valid_to"), at):
        raise MeshRefused(
            "outside_window",
            f"{at} is outside the operating window "
            f"[{config.get('valid_from')}, {config.get('valid_to')})",
        )
    return True


def filter_wire(
    lines: Sequence[Any] | None, my_nicks: Iterable[str] = ()
) -> tuple[list[WireLine], NoiseMeter]:
    """Drop wire noise before it reaches a mesh, and meter what was dropped."""
    meter = NoiseMeter()
    kept: list[WireLine] = []
    for raw in lines or ():
        line = raw if isinstance(raw, WireLine) else WireLine(**raw)
        if meter.record(classify_wire_line(line, my_nicks)):
            kept.append(line)
    return kept, meter


def record_provenance(
    mesh: str, request: dict, outcome: dict
) -> dict[str, Any]:
    """Record one mesh execution as a content-addressed provenance node.

    ``mem20dreamz.ledger`` reports durability honestly: when braid is not
    reachable the node is recorded as NOT committed, with the reason, rather
    than silently skipped.
    """
    return dreamz_ledger.commit_raw(
        "write:mesh_execution",
        f"mesh:{mesh}",
        {
            "mesh": mesh,
            "request_keys": sorted(request),
            "outcome_keys": sorted(outcome),
            "error": outcome.get("error"),
        },
    )


# ---------------------------------------------------------------------------
# The one entry point the dispatcher calls.
# ---------------------------------------------------------------------------


def admit(
    mesh: str,
    config: dict,
    request: dict,
    mesh_dir: Path,
) -> tuple[Admission, list[WireLine]]:
    """Run every check for one mesh execution.

    Returns the admission record and the wire lines that survived filtering.
    Raises :class:`MeshRefused` if any check refuses.
    """
    tool = str(request.get("tool") or f"{TOOL_PREFIX}_{mesh}")
    naming = check_tool_name(tool)
    uses = check_intended_uses(request.get("intended_uses"))
    stub_issues = check_no_stubs(mesh_dir)
    window_ok = check_operating_window(config, request.get("at"))
    kept, meter = filter_wire(request.get("wire"), request.get("my_nicks") or ())
    report = meter.report()

    admission = Admission(
        mesh=mesh,
        tool=tool,
        naming=naming,
        intended_uses=uses,
        wire_kept=len(kept),
        wire_swallowed=report.get("swallowed", 0),
        wire_waste_ratio=meter.waste_ratio,
        wire_reasons=dict(report.get("by_reason", {})),
        stub_issues=stub_issues,
        window_ok=window_ok,
    )
    return admission, kept
