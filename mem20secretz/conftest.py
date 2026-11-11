"""Package conftest: make `import mem20secretz` resolve to the real package.

The failure this fixes
----------------------
Running pytest against this project from the estate root fails at collection:

    mem20secretz/tests/test_sweep.py:13: in <module>
        from mem20secretz.sweep import (
    E   ModuleNotFoundError: No module named 'mem20secretz.sweep'

`sweep.py` exists, at `src/mem20secretz/sweep.py`. The import fails because
`import mem20secretz` resolves to the *outer* project directory
`<estate>/mem20secretz/`, which has no `__init__.py` and therefore matches as an
implicit namespace package. A namespace package has no `sweep` submodule, so the
`from ... import` fails even though the file is right there.

Why the estate root conftest does not already fix it
----------------------------------------------------
`<estate>/conftest.py` applies exactly this correction, but it only loads when
the estate root is the pytest rootdir. This project carries its own
`[tool.pytest.ini_options]` in `pyproject.toml`, so pytest selects
`<estate>/mem20secretz` as rootdir and never loads the estate conftest. The
sibling `mem20autouez` hit the same thing and fixed it the same way; this file
is that fix, applied to the src/ layout.

The fix
-------
Drop the estate root from sys.path so it cannot contribute a namespace portion,
lead with this project's `src/` (where the real package lives) and then the
project root, and purge a namespace entry cached before this ran.

Adding `__init__.py` to the outer directory would be the wrong fix: it would
turn the project directory into a package containing a package.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

# 1. The estate root must not contribute a namespace portion.
sys.path[:] = [p for p in sys.path if p not in ("", ".", _ESTATE_ROOT)]

# 2. src/ leads (the real package is there), then the project root.
for _candidate in (os.path.join(_PROJECT_ROOT, "src"), _PROJECT_ROOT):
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)

# 3. Drop a stale namespace entry if one was cached before this fix ran.
_mod = sys.modules.get("mem20secretz")
if (_mod is not None and getattr(_mod, "__file__", None) is None
        and getattr(_mod, "__path__", None) is not None):
    del sys.modules["mem20secretz"]
