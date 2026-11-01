"""Tests for mem20_mcp's forwarding contract.

The package's entire purpose is to be a thin, honest forwarder to the canonical
MCP tree at /opt/mem20/mcp. The failure that matters is subtle and quiet: if the
forwarder ever falls back to a local copy, the estate runs stale tool logic while
appearing healthy. So these tests are mostly about the refusal to do that.

``MEM20_CANONICAL_MCP_ROOT`` exists precisely so the canonical root can be
redirected at a fixture tree; the real default is exercised too.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ``mem20_mcp/__init__.py`` resolves the canonical root at import time, so on a
# box without /opt/mem20/mcp the bare ``import mem20_mcp`` below raises
# ImportError and pytest reports a collection ERROR for the whole module. That
# is the forwarder behaving correctly -- there is no canonical tree to forward
# to -- but it is not a test failure, and it made the suite unrunnable in a
# fresh clone. Skip the module instead, and say why.
try:
    import mem20_mcp
    from mem20_mcp import _forward
except ImportError as _exc:  # pragma: no cover - only without a canonical tree
    pytest.skip(
        f"no canonical MCP tree to forward to ({_exc})",
        allow_module_level=True,
    )

REAL_ROOT = Path("/opt/mem20/mcp")
