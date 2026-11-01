"""The five admission checks, each delegated to the subsystem that owns the rule.

Nothing here invents a policy. Every check calls the module that already owns
that rule in the estate, so the MCP surface cannot drift from the rest of the
fleet: if a linter tightens, admission tightens with it.

* naming        -> ``mem20ops.clicheck.classify_naming``
* body          -> ``mem20verify.linters.noop_bodies`` / ``identical_branches``
* intended use  -> ``mem20liez.gates.check_prohibited_uses``
* notification  -> ``mem20ircz.filter.classify``
* temporal      -> ``mem20temporaldatabasefabricz.temporal.interval.contains``
"""

from __future__ import annotations

import ast
import re
from typing import Iterable, Optional

from estate import Check

# Imported at module scope on purpose: a missing subsystem must fail loudly at
# import rather than degrade a check to a silent pass. A surface that admits
# tools because a linter could not be found is worse than one that will not start.
from mem20ircz.filter import classify as classify_irc_line
from mem20liez.gates import check_prohibited_uses
from mem20ops.clicheck import classify_naming
from mem20temporaldatabasefabricz.temporal.interval import contains as interval_contains
from mem20verify.linters import identical_branches, noop_bodies

#: Naming verdicts the fleet contract accepts for a subsystem binary.
ACCEPTED_NAMING = frozenset({"mem20-native", "fs-standard"})

#: The MCP tool-name shape: lowercase snake_case, optionally namespaced with a
#: single dot (``memory.recall``). This is the MCP convention, not the fleet
#: binary convention -- a tool is not a binary, so ``classify_naming`` is applied
#: to the *server* identity and this pattern to the tool name.
TOOL_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)?$")


def check_naming(tool: str, server_name: str = "mem20-mcp") -> Check:
    """The server must be a fleet-recognised binary and the tool a valid MCP name.

    Two different conventions, deliberately kept apart: ``classify_naming``
    answers "is this a mem20 subsystem binary?" and is applied to the server;
    the tool name is checked against the MCP snake_case shape. Applying the
    binary rule to a tool name would refuse every legitimate tool in the
    registry, which is the opposite of admission control.
    """
    server_verdict = classify_naming(server_name)
    if server_verdict not in ACCEPTED_NAMING:
        return Check(
            "naming",
            False,
            f"server '{server_name}' is '{server_verdict}'; expected one of "
            f"{sorted(ACCEPTED_NAMING)}",
        )
    if not TOOL_NAME_RE.match(tool):
        return Check(
            "naming",
            False,
            f"tool '{tool}' is not a valid MCP tool name (expected lowercase "
            f"snake_case, e.g. memory_store)",
        )
    return Check("naming", True, f"{tool} is a valid MCP tool name on {server_name}")


def check_handler_source(tool: str, source: str, path: str = "<tool>") -> Check:
    """The handler's real source must not be a stub.

    ``noop_bodies`` catches a body that is only ``pass``; ``identical_branches``
    catches an ``if``/``else`` that returns the same thing either way. Both are
    the shapes a placeholder takes when it is written to satisfy a schema.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return Check("body", False, f"{path} does not parse: {exc.msg} (line {exc.lineno})")

    issues = list(noop_bodies(path, tree)) + list(identical_branches(path, tree))
    if not issues:
        return Check("body", True, f"{path} has no stub-shaped body")
    detail = "; ".join(f"line {i.line}: {i.message}" for i in issues[:3])
    return Check("body", False, f"{len(issues)} stub-shaped construct(s): {detail}")


def check_intended_uses(uses: Optional[Iterable[str]]) -> Check:
    """Run the behavioural-signal prohibited-use gate over declared uses.

    The gate matches on a normalised key (``employment_screening_without_notice``),
    so a free-text use is normalised the same way before it is offered. Passing
    prose straight through would let every prohibited use slip past a check that
    only ever compares against snake_case keys.
    """
    declared = list(uses or [])
    if not declared:
        return Check("intended-use", True, "no behavioural-signal use declared")
    normalised = [u.strip().lower().replace(" ", "_") for u in declared]
    try:
        check_prohibited_uses(normalised)
    except Exception as exc:  # GateError and subclasses
        return Check("intended-use", False, f"{type(exc).__name__}: {exc}")
    return Check("intended-use", True, f"{len(declared)} declared use(s) permitted")


class _WireLine:
    """The slice of a parsed IRC line that ``mem20ircz.filter.classify`` reads.

    The filter is written against the daemon's parsed ``Message``; admission only
    needs the attributes it actually touches, so this stands in for a full parse
    without pretending to be one.
    """

    __slots__ = ("command", "text", "target", "is_channel", "params")

    def __init__(self, command: str, text: str = "", target: str = "",
                 is_channel: bool = False, params: tuple[str, ...] = ()) -> None:
        self.command = command
        self.text = text
        self.target = target
        self.is_channel = is_channel
        self.params = params


def check_notification(line: str, my_nicks: Iterable[str] = ()) -> Check:
    """Decide whether one wire line is worth forwarding to an agent.

    ``line`` is a raw IRC protocol line. The command is the first token after an
    optional ``:prefix``; a numeric command is kept as text because the filter
    compares numerics as strings.
    """
    raw = line.strip()
    if not raw:
        return Check("notification", False, "empty line")
    # Drop the optional ``:prefix`` (the sender) before reading the command.
    body = raw.split(" ", 1)[1] if raw.startswith(":") else raw
    parts = body.split(" ", 1)
    command = parts[0].upper()
    rest = parts[1] if len(parts) > 1 else ""
    text = rest.split(" :", 1)[1] if " :" in rest else ""
    target = rest.split(" ", 1)[0] if rest else ""
    verdict = classify_irc_line(
        _WireLine(command, text=text, target=target,
                  is_channel=target[:1] in "#&+!", params=tuple(rest.split())),
        my_nicks,
    )
    return Check("notification", bool(verdict), f"{command}: {verdict.reason}")


def check_temporal_window(valid_from: Optional[str], valid_to: Optional[str],
                          at: str) -> Check:
    """A time-boxed tool is admitted only while ``at`` is inside its interval."""
    if valid_from is None and valid_to is None:
        return Check("temporal", True, "no validity window declared")
    inside = interval_contains(valid_from, valid_to, at)
    window = f"[{valid_from or '-inf'}, {valid_to or '+inf'}]"
    if inside:
        return Check("temporal", True, f"{at} is inside {window}")
    return Check("temporal", False, f"{at} is outside {window}")
