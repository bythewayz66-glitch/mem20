"""Root package shim for mem20rpgz. Implementation in mem20rpgz.mem20rpgz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20rpgz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20rpgz.mem20rpgz import *  # noqa: F401,F403
    from mem20rpgz.mem20rpgz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
