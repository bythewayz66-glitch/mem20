import os, sys
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
_pkg = os.path.join(_root, "mem20core")
if _pkg not in sys.path:
    sys.path.insert(0, _pkg)
from mem20core.fixes import *  # noqa: F401,F403
from mem20core.fixes import patch as _patch; _patch()
