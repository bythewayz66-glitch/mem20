"""Package conftest: make the mem20 packages resolve to their real modules.

Two problems, both caused by the estate layout ``<project>/<name>/``:

1. **Namespace shadowing.** The outer project directory ``mem20shopz/`` has no
   ``__init__.py``. When the estate root is on ``sys.path``, Python matches that
   directory as a namespace package and it shadows the real installed package,
   producing a module with ``__file__ = None`` and no exported names. The estate
   root conftest fixes this globally, but it only loads when the estate root is
   the pytest rootdir. This package declares its own rootdir (see
   ``[tool.pytest.ini_options]`` in pyproject.toml), so apply the same
   correction here.

2. **Sibling packages are not importable.** ``mem20shopz.wiring`` uses six other
   mem20 subsystems. Under a package-local rootdir none of their project roots
   are on ``sys.path``, so the wiring tests would fail on import rather than on
   behaviour. Add each sibling project root explicitly.

The sibling list is deliberately explicit rather than a glob over the estate:
the wiring module has a fixed, reviewable dependency surface, and a test run
should not silently pick up a different set of packages than the code imports.
"""

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
_ESTATE_ROOT = os.path.dirname(_PROJECT_ROOT)

#: Project roots the wiring module imports from, relative to the estate root.
#: ``mem20sitemapz`` keeps its package under ``src/``.
_SIBLING_ROOTS = (
    "mem20famz",
    "mem20kanbanz",
    "mem20teamz",
    "mem20cliz",
    "memory_engine",
    os.path.join("mem20sitemapz", "src"),
)

# 1. the estate root must not be able to form namespace portions
sys.path[:] = [p for p in sys.path if p not in ("", ".", _ESTATE_ROOT)]

# 2. this project root first, then each sibling project root
for _rel in reversed(_SIBLING_ROOTS):
    _path = os.path.join(_ESTATE_ROOT, _rel)
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.insert(0, _path)

if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# 2b. ``memory_engine`` is a real package (it has an ``__init__.py``) that lives
#     directly at the estate root, so the estate root has to be importable for
#     ``memory_engine.memory``. Append it LAST: the ``mem20*`` project roots
#     above must stay ahead of it, or the outer project directories would win
#     the namespace-package match again.
if _ESTATE_ROOT not in sys.path:
    sys.path.append(_ESTATE_ROOT)

# 3. purge namespace-package entries cached before this file ran
for _name, _module in list(sys.modules.items()):
    if _name.startswith("mem20") or _name in {"memory_engine"}:
        if getattr(_module, "__file__", None) is None and getattr(_module, "__path__", None) is not None:
            del sys.modules[_name]
