"""Package conftest: make `import mem20api` resolve to the real package.

The failure this fixes
----------------------
Running pytest against this project from the estate root fails at collection:

    mem20api/tests/test_http_server.py:19: in <module>
        from mem20api.http_server import (
    E   ModuleNotFoundError: No module named 'mem20api.http_server'

`http_server.py` exists, at `mem20api/http_server.py` inside the package
directory. The import fails because `import mem20api` resolves to the *outer*
project directory `<estate>/mem20api/`, which has no `__init__.py` and therefore
matches as an implicit namespace package. A namespace package has no
`http_server` submodule, so the `from ... import` fails even though the file is
right there.

Why the estate root conftest does not already fix it
----------------------------------------------------
`<estate>/conftest.py` applies exactly this correction, but it only loads when
the estate root is the pytest rootdir. This project carries its own
`[tool.pytest.ini_options]` in `pyproject.toml`, so pytest selects
`<estate>/mem20api` as rootdir and never loads the estate conftest.

The CI job for this package works around it with `PYTHONPATH=mem20api` on the
command line (see the `mem20api` job in `.github/workflows/ci.yml`). That makes
the CI job green and leaves every other invocation - the conformance gate, a
plain `pytest mem20api`, a whole-estate run - failing. A conftest fixes the
project rather than one caller.

The fix
-------
Drop the estate root from sys.path so it cannot contribute a namespace portion,
lead with this project root (the package sits directly inside it, not under
src/), and purge a namespace entry cached before this ran.

Adding `__init__.py` to the outer directory would be the wrong fix: it would
turn the project directory into a package containing a package.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

# 1. The estate root must not contribute a namespace portion.
sys.path[:] = [p for p in sys.path if p not in ("", ".", _ESTATE_ROOT)]

# 2. This project root leads: the real package is directly inside it.
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 3. Drop a stale namespace entry if one was cached before this fix ran.
_mod = sys.modules.get("mem20api")
if (_mod is not None and getattr(_mod, "__file__", None) is None
        and getattr(_mod, "__path__", None) is not None):
    del sys.modules["mem20api"]
