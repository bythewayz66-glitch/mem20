"""Root package shim for mem20dreamz. Implementation in mem20dreamz.mem20dreamz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20dreamz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20dreamz.mem20dreamz import *  # noqa: F401,F403
    from mem20dreamz.mem20dreamz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
