from __future__ import annotations

import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"


def pytest_configure(config):  # noqa: ARG001 - pytest hook signature
    text = str(SRC_DIR)
    if text in sys.path:
        sys.path.remove(text)
    sys.path.insert(0, text)
