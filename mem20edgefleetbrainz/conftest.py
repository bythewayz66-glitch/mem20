"""Package conftest: make ``import mem20edgefleetbrainz`` resolve to the real package.

The estate root ``/opt/mem20`` holds the outer project directory
``mem20edgefleetbrainz/`` which has no ``__init__.py``. When pytest runs with
the estate root on ``sys.path``, Python matches that outer directory as a
namespace package and it shadows the real package nested one level down::

    ImportError: cannot import name 'FleetService' from 'mem20edgefleetbrainz'
                 (unknown location)

The estate root conftest fixes this for whole-estate runs, but this project
declares its own ``rootdir`` through ``[tool.pytest.ini_options]``, so it must
apply the correction itself. The logic is idempotent when both load.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

# 1. The estate root must not contribute a namespace portion for this package.
sys.path[:] = [
    path for path in sys.path
    if path not in ("", ".", _ESTATE_ROOT, _PROJECT_ROOT)
]

# 2. This project root leads, so the nested real package (with __init__.py) wins.
sys.path.insert(0, _PROJECT_ROOT)

# 3. Drop a stale namespace entry if pytest cached one before this ran.
_module = sys.modules.get("mem20edgefleetbrainz")
if (_module is not None
        and getattr(_module, "__file__", None) is None
        and getattr(_module, "__path__", None) is not None):
    del sys.modules["mem20edgefleetbrainz"]
