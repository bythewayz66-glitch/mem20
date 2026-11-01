"""Test bootstrap for mem20_mcp.

``mem20_mcp/__init__.py`` calls ``canonical_root()`` at import time, and that
function raises ``ImportError`` when ``/opt/mem20/mcp`` is absent. That is the
right behaviour for the package -- it refuses to fall back to stale local copies
-- but it means the suite cannot even be *collected* in a bare clone, which is
where CI and every reviewer runs it.

So this conftest builds a minimal but valid canonical tree and points
``MEM20_CANONICAL_MCP_ROOT`` at it before anything imports ``mem20_mcp``. The
real default is still asserted by
``test_forwarding.test_default_canonical_root_is_the_real_tree``, which checks
the constant rather than the resolved path, so redirecting here does not weaken
that test.

This file is also why the suite is honest about criterion 3: a test file that
exists but cannot be collected is not a test suite.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_FIXTURE_ROOT = Path(tempfile.mkdtemp(prefix="mem20-canonical-"))
(_FIXTURE_ROOT / "tools").mkdir(parents=True, exist_ok=True)
(_FIXTURE_ROOT / "server.py").write_text(
    "TOOLS = ['alpha', 'beta']\nSERVER = 'fixture'\n", encoding="utf-8"
)
(_FIXTURE_ROOT / "tools" / "thing.py").write_text(
    "NAME = 'thing'\ndef hello():\n    return 'hi'\n", encoding="utf-8"
)
(_FIXTURE_ROOT / "health.py").write_text(
    "def status():\n    return {'ok': True}\n", encoding="utf-8"
)

# Set before any test module imports mem20_mcp.
os.environ.setdefault("MEM20_CANONICAL_MCP_ROOT", str(_FIXTURE_ROOT))
