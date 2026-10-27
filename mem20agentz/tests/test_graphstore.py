"""Graph store / OREO parser tests — skip without mem20oreo (issue #30)."""
from __future__ import annotations

import pytest

pytest.importorskip(
    "mem20oreo",
    reason="mem20oreo gitlink not populated (docs/hygiene/oreo-gitlink.md, #30)",
)
