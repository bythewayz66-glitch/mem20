#!/usr/bin/env python3
"""mem20 Gateway — compatibility entry point.

This module used to be a near-verbatim copy of ``hermes_gateway.py``: 218 lines
duplicated, differing only in the word "Hermes" and in the generated agent-name
prefix (``hermes-`` here, ``mem20-`` there). Two copies of a relay is two places
for the admission policy to be forgotten, and the two had already drifted -- the
``hermes-`` prefix produced agent names that classify as "other", so agents
registered through that copy had addresses no other subsystem recognised.

There is now one implementation. This module re-exports it, so
``python3 -m mem20_gateway`` and ``from mem20_gateway import broadcast`` keep
working, and both go through the same admission control.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from hermes_gateway import (  # noqa: F401  (re-exported API)
    GATEWAY_DIR,
    MESSAGES_FILE,
    MEM20_DIR,
    NAMES_FILE,
    broadcast,
    ensure_dirs,
    list_agents,
    load_names,
    main,
    parse_args,
    read_messages,
    register_agent,
)

__all__ = [
    "GATEWAY_DIR",
    "MESSAGES_FILE",
    "MEM20_DIR",
    "NAMES_FILE",
    "broadcast",
    "ensure_dirs",
    "list_agents",
    "load_names",
    "main",
    "parse_args",
    "read_messages",
    "register_agent",
]

if __name__ == "__main__":
    raise SystemExit(main())
