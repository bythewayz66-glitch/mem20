"""Package conftest: make ``import mem20dreamz`` resolve to the real package.

The repository root holds the outer project directory ``mem20dreamz/`` (no
``__init__.py``). When pytest puts that root on ``sys.path``, Python matches the
outer directory as a namespace package and the real package is never found::

    ImportError: cannot import name 'seeds' from 'mem20dreamz' (unknown location)

The root conftest repairs this for whole-repository runs, but it does not load
when this package is the pytest rootdir (it declares its own ``testpaths`` in
``pyproject.toml``). Apply the same correction here, idempotently: lead with
this project root and drop the repository root so it cannot contribute a
namespace portion.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

sys.path[:] = [p for p in sys.path if p not in ("", ".", _ESTATE_ROOT)]

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

_mod = sys.modules.get("mem20dreamz")
if (_mod is not None and getattr(_mod, "__file__", None) is None
        and getattr(_mod, "__path__", None) is not None):
    del sys.modules["mem20dreamz"]
