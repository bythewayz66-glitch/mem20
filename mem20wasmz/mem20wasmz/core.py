import os, sys

# The shared substrate lives at <repo>/mem20core/mem20core, so the *package
# root* is <repo>/mem20core — not the repository root. Adding only the repo root
# makes `import mem20core` resolve to the directory (a namespace package with no
# submodules) and `from mem20core.fixes import *` then fails with
# ModuleNotFoundError. Add both so the shim works from a source checkout and
# from an installed distribution.
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for _p in (_root, os.path.join(_root, "mem20core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from mem20core.fixes import *  # noqa: F401,F403
from mem20core.fixes import patch as _patch; _patch()
