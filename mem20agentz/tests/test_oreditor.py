"""OREO editor tests — skipped without mem20oreo (issue #30)."""
from __future__ import annotations

import pytest

pytest.importorskip(
    "mem20oreo",
    reason="mem20oreo gitlink not populated (docs/hygiene/oreo-gitlink.md, #30)",
)

# Remaining tests exercise the real editor when the package is present.
# Collection no longer hard-fails on ModuleNotFoundError.
