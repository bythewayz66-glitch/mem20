"""Tool-surface admission control for the mem20 MCP server.

The MCP server is the one place where every other subsystem becomes reachable by
a client. That makes it the natural chokepoint for the estate's contracts, and
this module is that chokepoint: a tool is *admitted* to the surface only when it
passes the checks the rest of the estate already owns, rather than each tool
re-implementing them.

The checks themselves live in :mod:`checks` (one per owning subsystem) and the
verdict types in :mod:`estate`. This module composes them into a single verdict
and audits a live registry.

Every check returns a reason, so a refusal is diagnosable rather than a bare
``False``. Nothing here mutates the registry: :func:`admit_tool` reports, and
the caller decides.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from estate import Admission, Check
from checks import (
    check_handler_source,
    check_intended_uses,
    check_naming,
    check_notification,
    check_temporal_window,
)

__all__ = [
    "Admission",
    "Check",
    "admit_tool",
    "audit_registry",
    "check_handler_source",
    "check_intended_uses",
    "check_naming",
    "check_notification",
    "check_temporal_window",
    "main",
]


def admit_tool(tool: str, *, source: Optional[str] = None, path: str = "<tool>",
               intended_uses: Optional[Iterable[str]] = None,
               valid_from: Optional[str] = None, valid_to: Optional[str] = None,
               at: Optional[str] = None) -> Admission:
    """Run every applicable check for one tool and return the verdict.

    ``source`` is optional: a tool registered from a live handler object has no
    source text to lint, and skipping the body check is reported as a pass with
    the reason stated, not silently dropped.
    """
    checks = [check_naming(tool)]

    if source is None:
        checks.append(Check("body", True, "no source supplied; body not linted"))
    else:
        checks.append(check_handler_source(tool, source, path))

    checks.append(check_intended_uses(intended_uses))

    if at is not None or valid_from is not None or valid_to is not None:
        checks.append(check_temporal_window(valid_from, valid_to, at or ""))

    return Admission(tool=tool, checks=tuple(checks))


def audit_registry(tools: dict[str, Any], *, at: Optional[str] = None) -> dict[str, Any]:
    """Admit every tool in a live registry and summarise the result.

    ``tools`` is the server's ``self.tools`` mapping. Only names are checked
    here: the handlers are already imported objects, so there is no source text
    to lint without re-reading files, and inventing a pass would be worse than
    reporting that the body check did not run.
    """
    admissions = [admit_tool(name, at=at) for name in sorted(tools)]
    refused = [a for a in admissions if not a.admitted]
    return {
        "total": len(admissions),
        "admitted": len(admissions) - len(refused),
        "refused": len(refused),
        "refusals": [{"tool": a.tool, "reasons": [c.reason for c in a.refusals]}
                     for a in refused],
    }
