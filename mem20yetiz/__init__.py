"""Root package shim for mem20yetiz. Implementation in mem20yetiz.mem20yetiz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20yetiz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20yetiz.mem20yetiz import *  # noqa: F401,F403
    from mem20yetiz.mem20yetiz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
