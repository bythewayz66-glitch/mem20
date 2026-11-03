"""Unified memory engine surface.

The repo-root ``memory`` name IS the engine module, not a hand-maintained copy
of its API. ``import memory`` resolves to ``memory_engine.memory``:

* a copy drifts silently - a missing underscore re-export broke
  ``from memory import _detect_only``; and
* a copy breaks isolation: callers point ``memory.LEDGER`` /
  ``memory.VECTOR_INDEX`` at a temporary store, then the engine keeps writing
  through its own globals because only the copy was patched.

Data lives under ``MEM20_STORE_PATH`` (default ``~/.mem20/store``).
"""

import sys

from memory_engine import memory as _engine

sys.modules[__name__] = _engine
