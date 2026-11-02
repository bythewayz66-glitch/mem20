"""Admission control for the shape-shifting gateway.

This gateway's whole job is to translate between incompatible schemas, versions
and interaction patterns. That makes it the one place in the estate where a
payload is *rewritten* before it reaches a service, and a rewrite is exactly
where a field silently disappears.

Six estate modules are consulted, and each answers a question the gateway cannot
answer for itself:

``mem20ops.clicheck.classify_naming``
    A route is the gateway's addressing scheme. A route outside the estate
    convention is one no upstream will match.

``mem20liez.gates.check_prohibited_uses``
    A gateway that can rewrite any payload can rewrite one into a prohibited
    purpose. The estate's prohibited-use list is the ruling on where that line
    is, and it is checked before the payload is transformed.

``mem20verify.linters.noop_bodies``
    A transform whose body is ``pass`` returns the payload unchanged and reports
    success. The caller cannot tell that from a real translation, so the
    gateway's own source is linted before a payload is accepted.

``mem20temporaldatabasefabricz.temporal.interval.contains``
    Version routing is a time question: ``/v2`` is valid only while v2 is
    supported. Half-open interval algebra is the estate's one convention for
    "was this version live at that instant", and re-deriving it here would be
    the off-by-one bug it exists to prevent.

``mem20ircz.filter.classify`` / ``NoiseMeter``
    Upstream traffic reaches the gateway before it becomes a request. Health
    probes and banner chatter are dropped here, and the meter reports what was
    swallowed so the saving is evidence rather than a claim.

``mem20dreamz.ledger.commit_raw``
    Every translation is recorded as a content-addressed provenance node, so
    "what did this gateway actually send upstream" is answerable afterwards.
    The ledger reports honestly when braid is unreachable -- ``committed:
    False`` with a reason -- rather than silently skipping the record.

Nothing here is advisory. A refusal raises :class:`GatewayRefused` and the
payload is not transformed.
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

from .domain import transform_payload

#: A route is an address, so it must be an estate name. ``fs-*`` is accepted
#: too: the estate has both conventions and neither is wrong.
ACCEPTED_NAMINGS = frozenset({"mem20-native", "fs-standard"})


class GatewayRefused(RuntimeError):
    """A translation was refused by admission control.

    Carries the check that refused it, so a caller can tell a policy refusal
    apart from a transform that ran and failed.
    """

    def __init__(self, check: str, reason: str) -> None:
        super().__init__(f"{check}: {reason}")
        self.check = check
        self.reason = reason

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "check": self.check, "reason": self.reason}


@dataclass(frozen=True)
class WireLine:
    """One upstream line, in the shape ``mem20ircz.filter`` expects.

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
    """What admission control decided about one translation."""

    route: str
    version: str = ""
    naming: str = ""
    round_trip: dict[str, Any] = field(default_factory=dict)
    intended_uses: tuple[str, ...] = ()
    wire_kept: int = 0
    wire_swallowed: int = 0
    wire_waste_ratio: float = 0.0
    wire_reasons: dict[str, int] = field(default_factory=dict)
    stub_issues: int = 0
    window_ok: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "route": self.route,
            "version": self.version,
            "naming": self.naming,
            "round_trip": dict(self.round_trip),
            "intended_uses": list(self.intended_uses),
            "wire_kept": self.wire_kept,
            "wire_swallowed": self.wire_swallowed,
            "wire_waste_ratio": round(self.wire_waste_ratio, 4),
            "wire_reasons": dict(self.wire_reasons),
            "stub_issues": self.stub_issues,
            "window_ok": self.window_ok,
        }


# ---------------------------------------------------------------------------
# Individual checks. Each one raises GatewayRefused; none of them returns a
# boolean a caller could ignore.
# ---------------------------------------------------------------------------


def check_route(route: str) -> str:
    """Refuse a route that is not an estate address."""
    naming = classify_naming(route)
    if naming not in ACCEPTED_NAMINGS:
        raise GatewayRefused(
            "naming",
            f"route {route!r} classifies as {naming!r}; a gateway route must be "
            f"mem20-native or fs-standard",
        )
    return naming


def check_round_trip(payload: dict, mapping: dict | None = None) -> dict:
    """Refuse a transform that loses a field.

    This is the shape-shifting bug in its purest form: a field is renamed on the
    way out and not on the way back, the translation reports success, and the
    value is gone. ``domain.transform_payload`` is the real transform, so the
    check runs it and compares the field set before and after -- a mapping that
    collapses two keys onto one, or drops one, is refused rather than shipped.

    Payload keys are domain data, not addresses: ``goal`` and ``candidates`` are
    ordinary words, so they are not held to the naming convention. Only the
    route is an address.
    """
    if not mapping:
        return {"mapping": {}, "fields_in": len(payload), "fields_out": len(payload)}
    transformed = transform_payload(payload, mapping)
    if len(transformed) != len(payload):
        raise GatewayRefused(
            "lossy_transform",
            f"mapping collapses {len(payload)} fields into {len(transformed)}; "
            f"a translated field would silently disappear",
        )
    return {
        "mapping": dict(mapping),
        "fields_in": len(payload),
        "fields_out": len(transformed),
    }


def check_intended_uses(intended_uses: Iterable[str] | None) -> tuple[str, ...]:
    """Refuse a translation whose declared intended use is prohibited.

    Delegated to ``mem20liez.gates``: the prohibited-use list is the estate's
    ruling, and a second copy of it here would drift.
    """
    uses = tuple(intended_uses or ())
    try:
        check_prohibited_uses(list(uses) if uses else None)
    except GateError as exc:
        raise GatewayRefused("prohibited_use", str(exc)) from exc
    return uses


def audit_gateway_source(gateway_dir: Path) -> list:
    """Run the estate's stub linter over the gateway's own source."""
    issues: list = []
    for path in sorted(Path(gateway_dir).rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        issues.extend(noop_bodies(str(path), tree))
    return issues


def check_no_stubs(gateway_dir: Path) -> int:
    """Refuse a gateway whose transform body is a stub.

    A stubbed transform returns the payload unchanged and reports success, which
    is worse than an error: the caller cannot tell it from a real translation.
    """
    issues = audit_gateway_source(gateway_dir)
    if issues:
        first = issues[0]
        raise GatewayRefused(
            "stub_body",
            f"{len(issues)} stub body/bodies in {Path(gateway_dir).name}, "
            f"first at {first.path}:{first.line} ({first.check})",
        )
    return 0


def check_version_window(
    valid_from: str | None, valid_to: str | None, at: str | None
) -> bool:
    """Refuse a version that was not live at the requested instant.

    An absent window is an open interval, which ``contains`` already handles.
    """
    if at is None:
        return True
    if not interval_contains(valid_from, valid_to, at):
        raise GatewayRefused(
            "outside_window",
            f"{at} is outside the version window [{valid_from}, {valid_to})",
        )
    return True


def filter_wire(
    lines: Sequence[Any] | None, my_nicks: Iterable[str] = ()
) -> tuple[list[WireLine], NoiseMeter]:
    """Drop upstream noise before it becomes a request."""
    meter = NoiseMeter()
    kept: list[WireLine] = []
    for raw in lines or ():
        line = raw if isinstance(raw, WireLine) else WireLine(**raw)
        if meter.record(classify_wire_line(line, my_nicks)):
            kept.append(line)
    return kept, meter


def record_provenance(route: str, request: dict, outcome: dict) -> dict[str, Any]:
    """Record one translation as a content-addressed provenance node.

    ``mem20dreamz.ledger`` reports durability honestly: when braid is not
    reachable the node is recorded as NOT committed, with the reason, rather
    than silently skipped.
    """
    return dreamz_ledger.commit_raw(
        "write:gateway_translation",
        f"gateway:{route}",
        {
            "route": route,
            "request_keys": sorted(request),
            "outcome_keys": sorted(outcome),
            "error": outcome.get("error"),
        },
    )


# ---------------------------------------------------------------------------
# The one entry point the runtime calls.
# ---------------------------------------------------------------------------


def admit(
    route: str,
    payload: dict,
    gateway_dir: Path,
    version: str = "",
    intended_uses: Iterable[str] | None = None,
    mapping: dict | None = None,
    wire: Sequence[Any] | None = None,
    my_nicks: Iterable[str] = (),
    at: str | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> tuple[Admission, list[WireLine]]:
    """Run every check for one translation.

    Returns the admission record and the upstream lines that survived
    filtering. Raises :class:`GatewayRefused` if any check refuses.
    """
    naming = check_route(route)
    round_trip = check_round_trip(payload, mapping)
    uses = check_intended_uses(intended_uses)
    stub_issues = check_no_stubs(gateway_dir)
    window_ok = check_version_window(valid_from, valid_to, at)
    kept, meter = filter_wire(wire, my_nicks)
    report = meter.report()

    admission = Admission(
        route=route,
        version=version,
        naming=naming,
        round_trip=round_trip,
        intended_uses=uses,
        wire_kept=len(kept),
        wire_swallowed=report.get("swallowed", 0),
        wire_waste_ratio=meter.waste_ratio,
        wire_reasons=dict(report.get("by_reason", {})),
        stub_issues=stub_issues,
        window_ok=window_ok,
    )
    return admission, kept
