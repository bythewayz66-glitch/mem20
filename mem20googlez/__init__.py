"""Root package shim for mem20googlez. Implementation in mem20googlez.mem20googlez."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20googlez")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20googlez.mem20googlez import *  # noqa: F401,F403
    from mem20googlez.mem20googlez import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
