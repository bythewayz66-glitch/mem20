#!/usr/bin/env python3
"""Re-pin the ``requirements.lock`` editable installs to a given commit.

The four editable installs in ``requirements.lock`` point at a commit SHA of
this repository. ``scripts/check_lock_pin.py`` fails CI when those pins are
behind HEAD and the pinned package has changed since, so this is the companion
that fixes it.

Default target is HEAD. Because a commit cannot contain its own SHA, the
practical workflow is: commit your code, then run this and commit the lock --
the pin then names the commit that introduced the code it installs.

Usage:
    python3 scripts/repin_lock.py              # pin to HEAD
    python3 scripts/repin_lock.py --sha <sha>  # pin to an explicit commit
    python3 scripts/repin_lock.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCK = ROOT / "requirements.lock"

EDITABLE_PIN = re.compile(
    r"(?P<prefix>-e\s+git\+(?P<url>[^@\s]+)@)(?P<sha>[0-9a-fA-F]{7,40})"
    r"(?P<suffix>#egg=[A-Za-z0-9_.-]+(?:&subdirectory=[A-Za-z0-9_./-]+)?)"
)


def resolve(sha: str | None) -> str:
    target = sha or "HEAD"
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{target}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise SystemExit(f"::error::cannot resolve {target}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--sha", default=None, help="commit to pin (default: HEAD)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.lock.is_file():
        print(f"::error::{args.lock} not found")
        return 2

    sha = resolve(args.sha)
    original = args.lock.read_text(encoding="utf-8")

    changed = 0

    def _replace(match: re.Match[str]) -> str:
        nonlocal changed
        if match.group("sha") == sha:
            return match.group(0)
        changed += 1
        return f"{match.group('prefix')}{sha}{match.group('suffix')}"

    updated = EDITABLE_PIN.sub(_replace, original)

    if not changed:
        print(f"OK: every editable pin already names {sha}")
        return 0

    if args.dry_run:
        print(f"would re-pin {changed} editable install(s) to {sha}")
        return 0

    args.lock.write_text(updated, encoding="utf-8")
    print(f"re-pinned {changed} editable install(s) to {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
