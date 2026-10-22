#!/usr/bin/env python3
"""Run owebz pipeline — package path via specs/prod.md or MEM20_PACKAGE (issue #15)."""
import os
from pathlib import Path

DEFAULT_PACKAGE = os.environ.get("MEM20_PACKAGE", "specs/prod.md")

if __name__ == "__main__":
    pkg = Path(DEFAULT_PACKAGE)
    print(f"pipeline package: {pkg}")
