"""Crew runtime CLI, with status/doctor/simulate/serve depth commands."""
from __future__ import annotations
import sys
from typing import Optional, Sequence
from .runtime import main as runtime_main
from . import MEMBERS, __version__
def main(argv: Optional[Sequence[str]] = None) -> int:
    return runtime_main(argv)
if __name__ == "__main__":
    sys.exit(main())
