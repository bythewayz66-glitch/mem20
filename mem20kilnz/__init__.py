"""Root package shim for mem20kilnz. Implementation in mem20kilnz.mem20kilnz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20kilnz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20kilnz.mem20kilnz import *  # noqa: F401,F403
    from mem20kilnz.mem20kilnz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
