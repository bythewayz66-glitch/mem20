#!/usr/bin/env python3
"""Install every mem20 subsystem package into one interpreter (issue #227).

``toolchest`` marks a subsystem ``degraded`` when its distribution is not
visible to the interpreter that ran ``refresh``. That is an environment fact,
not a code defect, and it is fixed by installing the packages into the same
interpreter. This script does that in one pass, editable by default so the
registry and the working tree agree.

Usage:
    python scripts/install_estate.py --dry-run
    python scripts/install_estate.py
    python scripts/install_estate.py --python .venv/bin/python --continue-on-error
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories that are not installable subsystem projects.
SKIP_PREFIXES = ("mem20-sdk-",)
SKIP_SUFFIXES = (".egg-info",)


def discover_projects(root: Path = REPO_ROOT) -> list[Path]:
    """Return the project directories that carry a PEP-621 ``pyproject.toml``.

    The estate keeps each package at ``<project>/<package>/`` with the project
    metadata at the top level, so the pyproject's parent directory is the
    install target. Only ``mem20*`` directories are considered; the ``.egg-info``
    build artefacts are not projects even though they share the prefix.
    """
    projects = []
    for child in sorted(root.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        if not child.name.startswith("mem20"):
            continue
        if child.name.endswith(SKIP_SUFFIXES):
            continue
        if child.name.startswith(SKIP_PREFIXES):
            continue
        if (child / "pyproject.toml").is_file():
            projects.append(child)
    return projects


def install_command(python: str, project: Path, editable: bool, with_deps: bool) -> list[str]:
    """Build the pip argv for one project."""
    cmd = [python, "-m", "pip", "install"]
    if editable:
        cmd.append("--editable")
    if not with_deps:
        cmd.append("--no-deps")
    cmd.append(str(project))
    return cmd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="install_estate",
        description="Install every mem20 subsystem package into one interpreter.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpreter to install into (default: the one running this script)",
    )
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="checkout root to scan (default: the repository containing this script)",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        metavar="NAME",
        help="install only these projects; may be repeated",
    )
    parser.add_argument(
        "--no-editable",
        action="store_true",
        help="install a built copy instead of an editable install",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help="resolve each project's dependencies (default: --no-deps)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the commands without running them",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="keep installing after a failure and report the failures at the end",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        parser.error(f"root is not a directory: {root}")

    projects = discover_projects(root)
    if args.only:
        wanted = set(args.only)
        projects = [p for p in projects if p.name in wanted]
        missing = wanted - {p.name for p in projects}
        if missing:
            parser.error("unknown or uninstallable project(s): " + ", ".join(sorted(missing)))
    if not projects:
        print("no installable mem20* projects found", file=sys.stderr)
        return 1

    editable = not args.no_editable
    failures: list[tuple[str, int]] = []
    for project in projects:
        cmd = install_command(args.python, project, editable, args.with_deps)
        if args.dry_run:
            print(" ".join(cmd))
            continue
        result = subprocess.run(cmd, cwd=str(root))
        if result.returncode != 0:
            failures.append((project.name, result.returncode))
            print(f"FAILED {project.name} (exit {result.returncode})", file=sys.stderr)
            if not args.continue_on_error:
                break

    if args.dry_run:
        return 0

    installed = len(projects) - len(failures)
    print(f"installed {installed}/{len(projects)} project(s) into {args.python}")
    if failures:
        print("failed: " + ", ".join(f"{name} (exit {code})" for name, code in failures),
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
