"""Root conftest: stop the repo root from shadowing the nested mem20 packages.

The failure this fixes
----------------------
Running pytest from /opt/mem20 fails for the nested packages with:

    ImportError: cannot import name 'ActionSpec' from 'mem20unitiz'
                 (unknown location)

Cause: each package lives at <project>/<name>/, so the *outer* project
directory /opt/mem20/mem20unitiz has no __init__.py. When the repo root is on
sys.path (it is, because it is the cwd), Python matches that directory as a
namespace package and it wins over the correctly-installed real package. The
result is a module with __file__ = None and no exported names.

Adding __init__.py to the outer directories would be the wrong fix: it would
turn every project directory into a package containing a package.

The fix
-------
Drop the repo root from sys.path so it cannot contribute a namespace portion,
then put each project root on sys.path. The real package is then found either
via the editable install or via the project root. Verified to resolve
mem20unitiz and mem20googlez to their real __init__.py from the repo root.

The canonical way to run the estate's suites is still:

    mem20verify tests

which additionally honours per-package venvs and a per-package timeout.
"""

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

SKIP = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", "site-packages",
    "secrets", "backups", "data", "store", "build", "dist", "mem", "packaging",
    "roadmaps", "notes", "proof", "verification", "systemd", "docs",
}


def _project_roots():
    roots = []
    for name in sorted(os.listdir(ROOT)):
        if name in SKIP or name.startswith("."):
            continue
        path = os.path.join(ROOT, name)
        if not os.path.isdir(path):
            continue
        if os.path.exists(os.path.join(path, "pyproject.toml")) or \
                os.path.isfile(os.path.join(path, "__init__.py")) or \
                os.path.isdir(os.path.join(path, "tests")):
            roots.append(path)
    return roots


# 1. the repo root must not be able to form namespace portions
sys.path[:] = [p for p in sys.path if p not in ("", ".", ROOT)]

# 2. each real project root goes on the path instead
for _project in reversed(_project_roots()):
    if _project not in sys.path:
        sys.path.insert(0, _project)

# 3. Purge any namespace-package entries cached before this file ran.
#    A purge alone is not enough: pytest creates the bad entries *during* its
#    collection walk, which happens after this module is imported, so a
#    conftest-load purge has nothing to remove by then.
for _name, _module in list(sys.modules.items()):
    if _name.startswith("mem20") or _name in {"braid", "bpy", "mcp", "toolchest"}:
        _file = getattr(_module, "__file__", None)
        if _file is None and getattr(_module, "__path__", None) is not None:
            del sys.modules[_name]

# 3b. Re-import the INSTALLED mcp SDK and pre-bind it.
#     /opt/mem20/mcp is a project directory in this estate, so it lands on
#     sys.path during pytest's collection walk and matches `import mcp` as a
#     namespace package. That name collision then shadows the real SDK, and
#     mcp/memory_tools.py responds to the resulting ImportError by calling
#     sys.exit(1) - which aborts the entire session rather than skipping one
#     test. Binding the installed SDK here, while sys.path is still clean, makes
#     the later `import mcp` a cache hit so the shadow can never win.
try:
    import mcp as _real_mcp
    if getattr(_real_mcp, "__file__", None) is None:
        raise ImportError("mcp resolved to a namespace package, not the SDK")
except ImportError:
    pass  # SDK genuinely absent: the mcp suite cannot run here, say so per-test.

# 4. Proactively import each real package so collection cannot shadow it.
#    Binding the real module into sys.modules first turns the later
#    `import mem20x` into a cache hit, so a bare namespace portion (no
#    __file__, no __path__ to src/) can never win. This is what deterministically
#    fixed mem20ucgz / mem20zimr collection errors and the mem20gamez
#    "no attribute DQNAgent" failure under the estate default
#    --import-mode=importlib, without changing that default.
def _importable(project):
    mod = os.path.basename(project).replace("-", "_")
    for candidate in (os.path.join(project, "src", mod), os.path.join(project, mod)):
        if os.path.isfile(os.path.join(candidate, "__init__.py")):
            return mod, os.path.dirname(candidate)
    return None


for _project in _project_roots():
    _found = _importable(_project)
    if not _found:
        continue
    _mod, _parent = _found
    if _parent not in sys.path:
        sys.path.insert(0, _parent)
    try:
        importlib.import_module(_mod)
    except Exception:
        # A package whose import needs optional native deps may not load here;
        # that is fine. We only need the ones pytest will import in this session
        # to be pre-bound, and any that fail still import normally on demand.
        pass

# 5. Never let an import-time sys.exit() abort the whole collection session.
#
# Several modules under mcp/ used to respond to a missing optional dependency by
# calling sys.exit(1) inside a module-scope `except ImportError:` guard (see
# mcp/server.py and the module-scope guards under mcp/tools/). That is not a
# collection error - pytest reports it as
#
#     INTERNALERROR> SystemExit: 1
#     mainloop: caught unexpected SystemExit!
#     no tests collected
#
# and exits with status 3. The consequence is that ONE absent dependency hides
# the entire suite, and `pytest --collect-only` stops being a usable answer to
# "how many tests do we have". It also makes the failure look like a pytest bug
# rather than a missing requirement, which is why it took so long to attribute.
#
# The guards themselves are fixed to raise instead of exit, but this hook keeps
# the property true for any module added later: a SystemExit raised while
# importing a collection target is turned into a normal, reported collection
# error, so the rest of the session still runs and still reports `collected`.
import pytest as _pytest


@_pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector):
    """Report an import-time SystemExit as a collection error instead of dying."""
    outcome = yield
    try:
        outcome.get_result()
    except SystemExit as _exc:
        _report = _pytest.CollectReport(
            nodeid=collector.nodeid,
            outcome="failed",
            longrepr=(
                "SystemExit(%r) was raised while importing this module at "
                "collection time. A module-scope `except ImportError:` guard is "
                "almost certainly calling sys.exit() (or exiting the process) "
                "instead of raising. Raise an ImportError and record the missing "
                "dependency's absence instead - exiting is only correct in a "
                "`__main__`/entry-point path, never at import." % (_exc.code,)
            ),
            result=[],
        )
        _report.collector = collector
        outcome.force_result(_report)
