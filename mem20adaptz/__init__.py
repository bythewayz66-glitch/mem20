"""Root package shim for mem20adaptz. Implementation in mem20adaptz.mem20adaptz."""
from __future__ import annotations
import os as _os
# ensure inner package dir is on path for submodule resolution (cli, domain, etc.)
_inner = _os.path.join(_os.path.dirname(__file__), "mem20adaptz")
__path__ = [_inner] + list(__path__)  # type: ignore

# re-export common API from inner package
try:
    from mem20adaptz.mem20adaptz import *  # noqa: F401,F403
    from mem20adaptz.mem20adaptz import __all__ as _inner_all  # noqa: F401
    __all__ = list(_inner_all)
except Exception:
    __all__ = []
