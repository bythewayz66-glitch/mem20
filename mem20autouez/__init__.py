"""Root package shim for mem20autouez. Implementation in mem20autouez.mem20autouez."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20autouez")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20autouez.mem20autouez import *  # noqa: F401,F403
    from mem20autouez.mem20autouez import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
