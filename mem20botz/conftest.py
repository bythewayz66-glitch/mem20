"""Package conftest: make `import mem20botz` resolve to the real package.

The estate root /opt/mem20 holds the outer project directory
``mem20botz/`` (no ``__init__.py``). When pytest runs with the estate
root on sys.path, Python matches that outer directory as a namespace
package and it shadows the real installed package::

    AttributeError: module 'mem20botz' has no attribute '__version__'

The estate root conftest fixes this globally, but it only loads when the
estate root is the pytest rootdir. This package declares its own rootdir
(see ``[tool.pytest.ini_options]`` in pyproject.toml, the same stanza the
sibling packages carry), so apply the same correction here: drop the
estate root from sys.path and lead with this project root. Idempotent
with the root conftest when both load during whole-estate runs.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

# 1. The estate root must not contribute a namespace portion.
sys.path[:] = [p for p in sys.path if p not in ("", ".", _ESTATE_ROOT)]

# 2. This project root leads, so the real package (with __init__.py) wins.
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 3. Drop a stale namespace entry if one was cached before this fix ran.
_mod = sys.modules.get("mem20botz")
if (_mod is not None and getattr(_mod, "__file__", None) is None
        and getattr(_mod, "__path__", None) is not None):
    del sys.modules["mem20botz"]

# 4. Sibling packages this project imports are not pip-installed here either.
#    mem20botz.kanban_bot imports mem20kanbanz, so a package-only pytest run
#    (this file's own rootdir) must be able to resolve it from the repository.
#    Lead with each sibling's project root, never the repository root, so no
#    outer directory can shadow a real package.
_ESTATE_DIR = os.path.dirname(_PROJECT_ROOT)
if os.path.isdir(_ESTATE_DIR):
    for _entry in sorted(os.listdir(_ESTATE_DIR)):
        _sibling = os.path.join(_ESTATE_DIR, _entry)
        if not os.path.isdir(_sibling):
            continue
        for _candidate in (os.path.join(_sibling, "src", _entry),
                           os.path.join(_sibling, _entry)):
            if os.path.isfile(os.path.join(_candidate, "__init__.py")):
                _root = os.path.dirname(_candidate)
                if _root not in sys.path:
                    sys.path.insert(0, _root)
                break
