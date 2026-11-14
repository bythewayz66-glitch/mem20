"""Root package shim for mem20wasmz. Implementation in mem20wasmz.mem20wasmz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20wasmz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20wasmz.mem20wasmz import *  # noqa: F401,F403
    from mem20wasmz.mem20wasmz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
