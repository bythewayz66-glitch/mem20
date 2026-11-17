#!/usr/bin/env python3
"""Fail when the version is stated in more than one place and the places disagree.

mem20 states its version in three files:

  VERSION                              -- the release marker, authoritative
  pyproject.toml  [project] version    -- what `pip install .` records
  sdk/cpp/include/mem20/version.hpp    -- what the C++ SDK was built against

On 2026-11-01 these read 3.1.2, 3.0.0 and 3.1.0. Nothing compared them, so the
package metadata had been two minor releases behind the tree it described and
the SDK baseline one behind. This script is the comparison.

VERSION is authoritative because it is the file the release process writes and
the only one that is a single token with no surrounding syntax to parse.

Exit 0 when all three agree, 1 when they do not, 2 when a file is missing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_version_file() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def read_pyproject() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # Only the [project] table's version, not a dependency pin that happens to
    # look like a version.
    m = re.search(r'^\[project\][^\[]*?^version\s*=\s*"([^"]+)"', text, re.M | re.S)
    if not m:
        raise SystemExit("pyproject.toml: no [project] version found")
    return m.group(1)


def read_cpp_baseline() -> str:
    text = (ROOT / "sdk/cpp/include/mem20/version.hpp").read_text(encoding="utf-8")
    m = re.search(r'kServerBaseline\s*=\s*"([^"]+)"', text)
    if not m:
        raise SystemExit("version.hpp: no kServerBaseline found")
    return m.group(1)


def main() -> int:
    try:
        authoritative = read_version_file()
        pyproject = read_pyproject()
        cpp = read_cpp_baseline()
    except FileNotFoundError as e:
        print(f"::error::version check could not read a file: {e}")
        return 2

    print(f"VERSION                            {authoritative}")
    print(f"pyproject.toml [project] version   {pyproject}")
    print(f"sdk/cpp version.hpp kServerBaseline {cpp}")

    bad = []
    if pyproject != authoritative:
        bad.append(f"pyproject.toml says {pyproject}, VERSION says {authoritative}")
    if cpp != authoritative:
        bad.append(f"version.hpp says {cpp}, VERSION says {authoritative}")

    if bad:
        for b in bad:
            print(f"::error::version drift: {b}")
        print("Fix: set every file to the value in VERSION, or bump VERSION first.")
        return 1

    print(f"OK: all three agree on {authoritative}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
