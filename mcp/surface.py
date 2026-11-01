"""Tool-surface admission control for the mem20 MCP server.

A tool is not on the MCP surface because somebody added it to a list. It is on
the surface because the estate's own rules admit it, and every one of those
rules already exists as a module in this repository:

* **naming** -- ``mem20ops.clicheck.classify_naming`` decides whether a tool
  name is a mem20-native name or something that leaked in from elsewhere.
* **stub-shaped bodies** -- ``mem20verify.linters.noop_bodies`` parses the tool
  source and refuses a handler whose body is only ``pass``.
* **prohibited behavioural uses** -- ``mem20liez.gates.check_prohibited_uses``
  raises for a tool that declares a use the estate has ruled out.
* **wire noise** -- ``mem20ircz.filter.classify`` decides whether a line is
  something a person said or protocol chatter; a tool that only ever sees
  chatter is not worth a slot on the surface.
* **time-boxed validity** -- ``mem20temporaldatabasefabricz``'s
  ``interval.contains`` decides whether the tool is inside its declared
  validity window at the instant of admission.

The point of routing through those modules rather than re-implementing the
checks here is that the surface cannot drift from the estate: fix a linter, and
the surface tightens with it.

Everything in this module is pure and read-only. It parses text, calls the
estate functions, and returns a verdict. It never imports the MCP SDK, so it is
importable and testable without a live transport.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

# --- estate wiring -----------------------------------------------------------
# Imported at module scope on purpose: a missing dependency must fail loudly at
# import time, not silently degrade into "admitted because we could not check".
#
# The estate uses two layouts. ``mem20ops`` and ``mem20temporaldatabasefabricz``
# are src-layout (``<project>/src/<package>/``); ``mem20verify``, ``mem20liez``
# and ``mem20ircz`` are flat (``<project>/<package>/``). Neither is installed in
# this environment, so the project roots are put on sys.path here and the
# packages are imported by their real names. That keeps the import identical
# whether the caller is pytest, the CLI, or a plain ``python3`` from the repo
# root -- and it keeps the AST import names the conformance gate counts.
import sys as _sys
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).resolve().parents[1]
for _project in (
    "mem20ops", "mem20verify", "mem20liez", "mem20ircz",
    "mem20temporaldatabasefabricz",
):
    for _candidate in (_REPO_ROOT / _project / "src", _REPO_ROOT / _project):
        if _candidate.is_dir() and str(_candidate) not in _sys.path:
            _sys.path.insert(0, str(_candidate))

from mem20ops.clicheck import classify_naming
from mem20verify.linters import noop_bodies
from mem20liez.gates import GateError, check_prohibited_uses
from mem20ircz.filter import classify as classify_wire_line
from mem20temporaldatabasefabricz.temporal.interval import (
    contains as interval_contains,
)

#: Names that are structurally valid but carry no domain meaning. A tool called
#: ``helper`` is a sign the surface is being used as a scratchpad.
GENERIC_NAMES = frozenset({
    "helper", "helpers", "util", "utils", "misc", "stuff", "test", "tmp",
    "temp", "foo", "bar", "baz", "thing", "do", "run", "main", "handler",
})

#: A tool name must be a mem20-native name or an fs-standard name. Anything
#: else is reported by ``classify_naming`` as ``other`` and refused.
ACCEPTED_NAMINGS = frozenset({"mem20-native", "fs-standard"})


@dataclass(frozen=True)
class Check:
    """One admission check and what it decided."""

    name: str
    ok: bool
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "reason": self.reason}


@dataclass(frozen=True)
class Admission:
    """The verdict for one tool."""

    tool: str
    checks: tuple[Check, ...] = ()
    refused: bool = False

    @property
    def admitted(self) -> bool:
        return not self.refused and all(c.ok for c in self.checks)

    @property
    def reasons(self) -> list[str]:
        return [f"{c.name}: {c.reason}" for c in self.checks if not c.ok]

    def explain(self) -> str:
        """Human-readable verdict: one line per check, then the summary."""
        verdict = "ADMITTED" if self.admitted else "REFUSED"
        width = max(len(c.name) for c in self.checks) if self.checks else 0
        lines = [f"tool: {self.tool}  ->  {verdict}"]
        for c in self.checks:
            mark = "pass" if c.ok else "FAIL"
            lines.append(f"  {c.name:<{width}}  {mark}  {c.reason}")
        return "\n".join(lines)

    def as_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "admitted": self.admitted,
            "checks": [c.as_dict() for c in self.checks],
            "reasons": self.reasons,
        }


def _now(at: str | None) -> str:
    """The instant to evaluate validity at, as an ISO-8601 UTC string."""
    if at:
        return at
    return datetime.now(timezone.utc).isoformat()


def check_name(tool: str) -> Check:
    """Naming check, delegated to ``mem20ops.clicheck.classify_naming``."""
    naming = classify_naming(tool)
    if tool.strip().lower() in GENERIC_NAMES:
        return Check("name", False, f"'{tool}' is a generic name, not a domain tool")
    if naming not in ACCEPTED_NAMINGS:
        return Check("name", False, f"'{tool}' classified as '{naming}'")
    return Check("name", True, naming)


def check_body(tool: str, source: str | None, path: str = "<tool>") -> Check:
    """Stub check, delegated to ``mem20verify.linters.noop_bodies``.

    A tool with no source supplied cannot be checked, and an unchecked handler
    is exactly the case this gate exists to stop, so it is refused rather than
    waved through.
    """
    if source is None:
        return Check("body", False, "no source supplied; handler cannot be verified")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return Check("body", False, f"source does not parse: {exc.msg} (line {exc.lineno})")
    issues = noop_bodies(path, tree)
    if issues:
        first = issues[0]
        return Check(
            "body", False,
            f"{len(issues)} noop body/bodies, first at line {first.line}: {first.message}",
        )
    return Check("body", True, "no stub-shaped handler bodies")


def check_uses(intended_uses: Sequence[str] | None) -> Check:
    """Prohibited-use check, delegated to ``mem20liez.gates.check_prohibited_uses``."""
    try:
        check_prohibited_uses(list(intended_uses) if intended_uses else None)
    except GateError as exc:
        return Check("uses", False, f"[{exc.code}] {exc.message}")
    return Check("uses", True, f"{len(intended_uses or ())} declared use(s) permitted")


def check_validity(valid_from: str | None, valid_to: str | None, at: str | None) -> Check:
    """Validity-window check, delegated to the temporal fabric's ``contains``."""
    instant = _now(at)
    try:
        inside = interval_contains(valid_from, valid_to, instant)
    except (ValueError, AssertionError) as exc:
        return Check("validity", False, f"unparseable window or instant: {exc}")
    if not inside:
        return Check(
            "validity", False,
            f"{instant} outside [{valid_from or '-inf'}, {valid_to or '+inf'})",
        )
    return Check("validity", True, f"{instant} inside the declared window")


def check_wire_noise(lines: Iterable[Any], my_nicks: Iterable[str] = ()) -> Check:
    """Signal check, delegated to ``mem20ircz.filter.classify``.

    A tool that declares the wire lines it consumes must consume at least one
    line a person actually said. A tool fed only numerics, NOTICEs and roster
    churn is a token sink, not a tool.
    """
    lines = list(lines)
    if not lines:
        return Check("signal", True, "no wire lines declared")
    kept = [ln for ln in lines if classify_wire_line(ln, my_nicks)]
    if not kept:
        return Check(
            "signal", False,
            f"all {len(lines)} declared wire line(s) are protocol noise",
        )
    return Check("signal", True, f"{len(kept)}/{len(lines)} declared line(s) carry signal")


def admit_tool(
    tool: str,
    *,
    source: str | None = None,
    path: str = "<tool>",
    intended_uses: Sequence[str] | None = None,
    valid_from: str | None = None,
    valid_to: str | None = None,
    at: str | None = None,
    wire_lines: Iterable[Any] | None = None,
    my_nicks: Iterable[str] = (),
) -> Admission:
    """Run every admission check for one tool and return the verdict.

    Checks run in a fixed order and all of them run, so a refusal reports every
    reason at once instead of one per round trip.
    """
    checks = (
        check_name(tool),
        check_body(tool, source, path),
        check_uses(intended_uses),
        check_validity(valid_from, valid_to, at),
        check_wire_noise(wire_lines or (), my_nicks),
    )
    return Admission(tool=tool, checks=checks, refused=not all(c.ok for c in checks))


def audit_registry(
    registry: Iterable[str],
    *,
    sources: dict[str, str] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    """Admit every tool in a registry and summarise the result.

    ``sources`` maps tool name to handler source. A tool with no entry is
    refused by the body check, which is the intended behaviour: the registry
    must be able to show the code it is admitting.
    """
    sources = sources or {}
    admissions = [
        admit_tool(name, source=sources.get(name), path=f"<{name}>", at=at)
        for name in registry
    ]
    admitted = [a.tool for a in admissions if a.admitted]
    refusals = [a for a in admissions if not a.admitted]
    return {
        "at": _now(at),
        "total": len(admissions),
        "admitted": len(admitted),
        "refused": len(refusals),
        "admitted_tools": admitted,
        "refusals": [{"tool": a.tool, "reasons": a.reasons} for a in refusals],
        "clean": not refusals,
    }
