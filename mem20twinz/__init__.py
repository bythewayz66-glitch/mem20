"""Root package shim for mem20twinz. Implementation in mem20twinz.mem20twinz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20twinz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20twinz.mem20twinz import *  # noqa: F401,F403
    from mem20twinz.mem20twinz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
