"""Admission control for the fleet relay.

The gateway is the one place in this estate where a message crosses from one
agent to another, and where a message can be posted *as a human*
(``send_human_message``). That makes it the estate's deception surface: a relay
that will carry anything is a relay that will carry an impersonation, and a
relay with no audit trail cannot tell you afterwards what it carried.

Six estate modules are consulted, and each answers a question the relay cannot
answer for itself:

``mem20liez.gates.check_prohibited_uses``
    ``send_human_message`` exists so an operator can speak into the fleet. It is
    also, structurally, impersonation. The estate's prohibited-use list is the
    ruling on where that line is, and it is checked before the message is
    written -- not left to each caller to remember.

``mem20ops.clicheck.classify_naming``
    Agent names are the addressing scheme. A name outside the estate convention
    is one no other subsystem will recognise, and the two gateway modules
    disagreed about it: ``hermes_gateway`` generated ``hermes-<loc>-<id>`` while
    ``mem20_gateway`` generated ``mem20-<loc>-<id>``. Both are "other" under the
    convention except the mem20 one, so the generator is fixed and new
    registrations are checked.

``mem20verify.linters.noop_bodies``
    A relay whose handler body is ``pass`` returns a well-formed entry that was
    never written. The linter runs over the gateway's own source before a
    message is accepted.

``mem20ircz.filter.classify`` / ``NoiseMeter``
    Inbound transport lines (IRC, telegram) reach the relay before they become
    messages. MOTD bursts and roster churn are dropped here, and the meter
    reports what was swallowed so the saving is evidence rather than a claim.

``mem20temporaldatabasefabricz.temporal.interval.contains``
    A relayed message carries a timestamp, and a replayed old message is
    indistinguishable from a new one unless the window is checked. Half-open
    interval algebra is the estate's one convention for that.

``mem20dreamz.ledger.commit_raw``
    Every accepted message is recorded as a content-addressed provenance node,
    so "what did the fleet actually say" is answerable after the fact. The
    ledger reports honestly when braid is unreachable -- ``committed: False``
    with a reason -- rather than silently skipping the record.

Nothing here is advisory. A refusal raises :class:`RelayRefused` and the message
is not written.
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

#: An agent name is an address, so it must be an estate name. ``fs-*`` is
#: accepted too: the estate has both conventions and neither is wrong.
ACCEPTED_NAMINGS = frozenset({"mem20-native", "fs-standard"})

#: Prefix the relay generates agent names under. ``hermes_gateway`` used
#: ``hermes-``, which classifies as "other" and is not an address any other
#: subsystem recognises.
AGENT_PREFIX = "mem20"

#: Message kinds that carry a human voice. These are the ones the prohibited-use
#: gate is most relevant to, so they are named rather than inferred.
HUMAN_VOICE_KINDS = frozenset({"human_message"})


class RelayRefused(RuntimeError):
    """A message was refused by relay admission control.

    Carries the check that refused it, so a caller can tell a policy refusal
    apart from a transport failure.
    """

    def __init__(self, check: str, reason: str) -> None:
        super().__init__(f"{check}: {reason}")
        self.check = check
        self.reason = reason

    def as_dict(self) -> dict[str, Any]:
        return {"refused": True, "check": self.check, "reason": self.reason}


@dataclass(frozen=True)
class WireLine:
    """One inbound transport line, in the shape ``mem20ircz.filter`` expects.

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
    """What relay admission control decided about one message."""

    agent_name: str
    kind: str
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
            "agent_name": self.agent_name,
            "kind": self.kind,
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
# Individual checks. Each one raises RelayRefused; none of them returns a
# boolean a caller could ignore.
# ---------------------------------------------------------------------------


def check_agent_name(name: str) -> str:
    """Refuse an agent name that is not an estate address."""
    naming = classify_naming(name)
    if naming not in ACCEPTED_NAMINGS:
        raise RelayRefused(
            "naming",
            f"agent name {name!r} classifies as {naming!r}; an agent name is an "
            f"address and must be mem20-native or fs-standard",
        )
    return naming


def generate_agent_name(location: str | None = None, agent_id: str = "") -> str:
    """Build an agent name that passes :func:`check_agent_name`.

    ``hermes_gateway`` generated ``hermes-<loc>-<id>``, which classifies as
    "other" -- so every agent it registered had an address no other subsystem
    recognised. ``mem20_gateway`` already used the ``mem20-`` prefix; this is
    that behaviour, in one place, for both.
    """
    short_loc = (location or "unknown").replace("/", "-").replace(" ", "-")[:20]
    suffix = agent_id or "00000000"
    return f"{AGENT_PREFIX}-{short_loc}-{suffix}"


def check_intended_uses(intended_uses: Iterable[str] | None) -> tuple[str, ...]:
    """Refuse a message whose declared intended use is prohibited.

    Delegated to ``mem20liez.gates``: the prohibited-use list is the estate's
    ruling, and a second copy of it here would drift.
    """
    uses = tuple(intended_uses or ())
    try:
        check_prohibited_uses(list(uses) if uses else None)
    except GateError as exc:
        raise RelayRefused("prohibited_use", str(exc)) from exc
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
    """Refuse a relay whose handler body is a stub.

    A stubbed handler returns a well-formed entry that was never written, which
    is worse than an error: the sender believes the fleet received it.
    """
    issues = audit_gateway_source(gateway_dir)
    if issues:
        first = issues[0]
        raise RelayRefused(
            "stub_body",
            f"{len(issues)} stub body/bodies in {Path(gateway_dir).name}, "
            f"first at {first.path}:{first.line} ({first.check})",
        )
    return 0


def check_message_window(
    valid_from: str | None, valid_to: str | None, at: str | None
) -> bool:
    """Refuse a message whose timestamp is outside its validity window.

    A replayed old message is indistinguishable from a new one unless the window
    is checked. An absent window is an open interval, which ``contains`` already
    handles.
    """
    if at is None:
        return True
    if not interval_contains(valid_from, valid_to, at):
        raise RelayRefused(
            "outside_window",
            f"{at} is outside the message window [{valid_from}, {valid_to})",
        )
    return True


def filter_wire(
    lines: Sequence[Any] | None, my_nicks: Iterable[str] = ()
) -> tuple[list[WireLine], NoiseMeter]:
    """Drop transport noise before it becomes a relayed message."""
    meter = NoiseMeter()
    kept: list[WireLine] = []
    for raw in lines or ():
        line = raw if isinstance(raw, WireLine) else WireLine(**raw)
        if meter.record(classify_wire_line(line, my_nicks)):
            kept.append(line)
    return kept, meter


def record_provenance(entry: dict) -> dict[str, Any]:
    """Record one accepted message as a content-addressed provenance node.

    ``mem20dreamz.ledger`` reports durability honestly: when braid is not
    reachable the node is recorded as NOT committed, with the reason, rather
    than silently skipped.
    """
    return dreamz_ledger.commit_raw(
        "write:gateway_message",
        f"gateway:{entry.get('agent_name', 'unknown')}",
        {
            "agent_name": entry.get("agent_name"),
            "kind": entry.get("type"),
            "target": entry.get("target") or entry.get("target_agent"),
            "message_id": entry.get("message_id"),
            "chars": len(str(entry.get("message", ""))),
        },
    )


# ---------------------------------------------------------------------------
# The one entry point the relay calls.
# ---------------------------------------------------------------------------


def admit(
    agent_name: str,
    kind: str,
    gateway_dir: Path,
    intended_uses: Iterable[str] | None = None,
    wire: Sequence[Any] | None = None,
    my_nicks: Iterable[str] = (),
    at: str | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> tuple[Admission, list[WireLine]]:
    """Run every check for one message.

    Returns the admission record and the transport lines that survived
    filtering. Raises :class:`RelayRefused` if any check refuses.
    """
    naming = check_agent_name(agent_name)
    uses = check_intended_uses(intended_uses)
    stub_issues = check_no_stubs(gateway_dir)
    window_ok = check_message_window(valid_from, valid_to, at)
    kept, meter = filter_wire(wire, my_nicks)
    report = meter.report()

    admission = Admission(
        agent_name=agent_name,
        kind=kind,
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
