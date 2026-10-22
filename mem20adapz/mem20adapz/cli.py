"""Adaptive runtime CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from . import FORMER_PACKAGES, MEMBERS, __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mem20adapz",
        description="mem20 adaptive systems runtime (consolidated organs).",
    )
    parser.add_argument("--version", action="store_true", help="Print version and exit.")
    parser.add_argument("--members", action="store_true", help="List absorbed members and exit.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"mem20adapz {__version__}")
    if args.members:
        for short, former in MEMBERS.items():
            print(f"{short}\t{former}")
    if not (args.version or args.members):
        print(f"mem20adapz {__version__} — {len(FORMER_PACKAGES)} absorbed adaptive organs")
        print("Use --members or --version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
