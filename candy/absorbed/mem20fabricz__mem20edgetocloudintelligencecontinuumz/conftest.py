"""Package conftest: make ``import mem20edgetocloudintelligencecontinuumz`` resolve.

The estate root holds the outer project directory which has no ``__init__.py``;
pytest can match it as a namespace package and shadow the real nested package.
Drop the estate root and lead with this project root. Idempotent with the root
conftest.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

sys.path[:] = [p for p in sys.path if p not in ("", ".", _ESTATE_ROOT, _PROJECT_ROOT)]
sys.path.insert(0, _PROJECT_ROOT)

_module = sys.modules.get("mem20edgetocloudintelligencecontinuumz")
if (_module is not None and getattr(_module, "__file__", None) is None
        and getattr(_module, "__path__", None) is not None):
    del sys.modules["mem20edgetocloudintelligencecontinuumz"]
