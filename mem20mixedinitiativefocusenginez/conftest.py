"""Package conftest: make `import mem20mixedinitiativefocusenginez` and
`import toolchest.catalog` both resolve from the estate root.

The failure this fixes
----------------------
Running pytest against this project from the estate root fails at collection:

    mem20mixedinitiativefocusenginez/.../domain.py:6: in <module>
        from toolchest.catalog import load_inventory
    E   ModuleNotFoundError: No module named 'toolchest.catalog'

`toolchest` is a sibling project in this estate with a src/ layout:
`toolchest/src/toolchest/catalog.py`. From the estate root, `import toolchest`
matches the *outer* directory `<estate>/toolchest/`, which has no `__init__.py`
and therefore matches as an implicit namespace package. A namespace package has
no `catalog` submodule, so the import fails even though the file is right there.

This is the same class of breakage as the two dead package names in the CI
green set, and it is not specific to this project: 50 `domain.py` modules across
the estate import `toolchest.catalog` the same way. Fixing it here fixes the
collection of this project; the other 49 need the same treatment or a shared
conftest, which is a decision for the owner rather than something to guess at.

Why the estate root conftest does not already fix it
----------------------------------------------------
`<estate>/conftest.py` puts each project root on sys.path, but for a src/ layout
the *package* lives one level deeper, at `<project>/src/<name>/`. Its
`_importable()` helper does handle that for the project's own package, but it
does not add `<project>/src` to sys.path for a *dependency* package that the
project imports. So `toolchest` is never resolvable as a package from here.

The fix
-------
Drop the estate root from sys.path so it cannot contribute a namespace portion,
lead with this project root, and add the sibling `toolchest/src` so the real
`toolchest` package wins over the outer directory. Purge any namespace entry
cached before this ran.

Adding `__init__.py` to the outer directories would be the wrong fix: it would
turn each project directory into a package containing a package.
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

# 3. The sibling src/ layout dependency must resolve to its real package.
_TOOLCHEST_SRC = os.path.join(_ESTATE_ROOT, "toolchest", "src")
if os.path.isdir(_TOOLCHEST_SRC) and _TOOLCHEST_SRC not in sys.path:
    sys.path.insert(0, _TOOLCHEST_SRC)

# 4. Drop stale namespace entries cached before this fix ran.
for _name in ("mem20mixedinitiativefocusenginez", "toolchest"):
    _mod = sys.modules.get(_name)
    if (_mod is not None and getattr(_mod, "__file__", None) is None
            and getattr(_mod, "__path__", None) is not None):
        del sys.modules[_name]
