#!/usr/bin/env python3
"""Fail when a ``requirements.lock`` editable pin is behind HEAD.

``requirements.lock`` pins the four editable installs (mem20agentz,
mem20controlz, mem20dreamz, mem20ops) to a commit SHA of this same repository:

    -e git+https://github.com/bythewayz66-glitch/mem20.git@<sha>#egg=...&subdirectory=...

Nothing compared that SHA against the tree it ships with, so the pins silently
fell behind. Issue #447 was exactly that: the lock still pointed at a commit
from before the 4.0.0 surface work, so a fresh ``pip install -r
requirements.lock`` installed a stale copy of those four packages while the
checkout said 4.0.0. Every other gate passed, because none of them read the
lock.

What "behind" means here
------------------------
A pin can never equal HEAD: the commit that writes the pin cannot contain its
own SHA, so a strict ``pin == HEAD`` rule is unsatisfiable and would be red on
every commit. The drift that actually hurts is narrower -- the pin is behind
HEAD *and* the pinned package has changed in the meantime, so the lock installs
code that is not what the tree contains.

So a pin passes when either:

  * it is HEAD, or
  * it is an ancestor of HEAD and no commit in ``<pin>..HEAD`` touched that
    pin's ``subdirectory=``.

It fails when the pin is behind and its subdirectory has moved since, when the
pin is not an ancestor of HEAD at all (rewritten/diverged history), or when the
pinned SHA is not in this clone.

Exit codes:
  0  every pin describes the current tree
  1  at least one pin is stale
  2  could not evaluate (no lock file, no git, unreadable pin)

Usage:
    python3 scripts/check_lock_pin.py
    python3 scripts/check_lock_pin.py --lock path/to/requirements.lock
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOCK = ROOT / "requirements.lock"

#: ``-e git+<url>@<sha>#egg=<name>&subdirectory=<dir>`` -- the SHA and the
#: subdirectory are what this check needs; the egg name makes a failure readable.
EDITABLE_PIN = re.compile(
    r"^\s*-e\s+git\+(?P<url>[^@\s]+)@(?P<sha>[0-9a-fA-F]{7,40})"
    r"#egg=(?P<egg>[A-Za-z0-9_.-]+)"
    r"(?:&subdirectory=(?P<subdir>[A-Za-z0-9_./-]+))?"
)


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def head_sha() -> str:
    completed = git("rev-parse", "HEAD")
    if completed.returncode != 0:
        raise SystemExit("::error::could not read HEAD: %s" % completed.stderr.strip())
    return completed.stdout.strip()


def object_exists(sha: str) -> bool:
    return git("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0


def is_ancestor(sha: str, of: str) -> bool:
    """True when ``sha`` is an ancestor of ``of`` (i.e. ``of`` has moved past it)."""
    return git("merge-base", "--is-ancestor", sha, of).returncode == 0


def commits_touching(sha: str, head: str, subdir: str | None) -> int:
    """How many commits in ``sha..head`` changed ``subdir`` (all of the tree if None)."""
    args = ["rev-list", "--count", f"{sha}..{head}"]
    if subdir:
        args += ["--", subdir]
    completed = git(*args)
    if completed.returncode != 0:
        return 0
    try:
        return int(completed.stdout.strip() or "0")
    except ValueError:
        return 0


def read_pins(lock: Path) -> list[tuple[str, str, str | None]]:
    pins: list[tuple[str, str, str | None]] = []
    for line in lock.read_text(encoding="utf-8").splitlines():
        match = EDITABLE_PIN.match(line)
        if match:
            pins.append(
                (match.group("egg"), match.group("sha"), match.group("subdir"))
            )
    return pins


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lock",
        type=Path,
        default=DEFAULT_LOCK,
        help="path to requirements.lock (default: repo root)",
    )
    args = parser.parse_args()

    if not args.lock.is_file():
        print("::error::%s not found" % args.lock)
        return 2

    try:
        head = head_sha()
    except SystemExit as exc:  # pragma: no cover - defensive
        print(exc)
        return 2

    pins = read_pins(args.lock)
    if not pins:
        print("::error::no editable git pins found in %s" % args.lock)
        return 2

    try:
        shown_lock = args.lock.relative_to(ROOT)
    except ValueError:
        shown_lock = args.lock
    print(f"HEAD  {head}")
    print(f"lock  {shown_lock}")

    problems: list[str] = []
    for egg, sha, subdir in pins:
        where = subdir or "."
        if sha == head:
            print(f"  OK       {egg:<16} {sha} (is HEAD)")
            continue
        if not object_exists(sha):
            problems.append(
                f"{egg} pins {sha}, which is not a commit in this clone "
                "(shallow clone, or a rewritten history)"
            )
            print(f"  MISSING  {egg:<16} {sha}")
            continue
        if not is_ancestor(sha, head):
            problems.append(
                f"{egg} pins {sha}, which is not an ancestor of HEAD {head} "
                "(diverged history)"
            )
            print(f"  DIVERGED {egg:<16} {sha}")
            continue
        behind = commits_touching(sha, head, None)
        moved = commits_touching(sha, head, subdir)
        if moved:
            problems.append(
                f"{egg} pins {sha}, which is {behind} commit(s) behind HEAD {head} "
                f"and {moved} of them changed {where}"
            )
            print(
                f"  STALE    {egg:<16} {sha} ({behind} behind, {moved} touching {where})"
            )
            continue
        print(
            f"  OK       {egg:<16} {sha} ({behind} behind, but {where} unchanged)"
        )

    if problems:
        for problem in problems:
            print(f"::error::stale lock pin: {problem}")
        print(
            "Fix: re-pin the editable installs to a commit that contains the "
            "current code --\n"
            "  python3 scripts/repin_lock.py   (or update the @<sha> in "
            "requirements.lock by hand)"
        )
        return 1

    print(f"OK: all {len(pins)} editable pin(s) describe the current tree at {head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
