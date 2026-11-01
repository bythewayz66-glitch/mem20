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
