# Ensure local package imports resolve under the estate root conftest.
import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
_pkg = os.path.abspath(os.path.join(_here, "..", ".."))  # project root
if _pkg not in sys.path:
    sys.path.insert(0, _pkg)
# purge stale namespace resolutions for this package
for _n in list(sys.modules):
    if _n == "mem20intenttomissioncompilerz" or _n.startswith("mem20intenttomissioncompilerz."):
        _m = sys.modules[_n]
        if getattr(_m, "__file__", None) is None:
            del sys.modules[_n]
