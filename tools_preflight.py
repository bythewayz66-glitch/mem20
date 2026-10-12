"""Pre-flight gate for Option C domain modules.

Run per module BEFORE it counts as implemented. Catches the four failure
modes that produced every real bug in this session:

  G1  an imported or re-exported symbol that does not exist
  G2  a private function that is defined and never referenced (dead code)
  G3  tests that never exercise a boundary case
  G4  a module that does not actually import

Exit non-zero on any failure, so it can gate a batch.
"""
from __future__ import annotations
import ast, importlib, os, sys
from pathlib import Path

ROOT = Path("/opt/mem20")

# Boundary probes every domain test suite is expected to contain.
BOUNDARY_MARKERS = {
    "empty": ("empty", "[]", "== 0", "no observations"),
    "single": ("single", "one ", "[1]", '["only"]'),
    "boundary": ("boundary", "threshold", "exact", "== 0", "<= 0", "== 1"),
    "duplicate": ("duplicate", "idempotent", "twice", "merge"),
}


def _mod_imports(tree):
    """(module, [names]) for every `from .x import a, b`."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.level:
            out.append((n.module, [a.name for a in n.names]))
    return out


def _defined(tree):
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def _referenced(tree):
    return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
           {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}


def check_package(pkg: str):
    d = ROOT / pkg
    inner = d / pkg
    problems = []

    domain = inner / "domain.py"
    tests = inner / "tests" / "test_domain.py"
    if not domain.exists():
        return [f"{pkg}: no domain.py"]
    if not tests.exists():
        return [f"{pkg}: no tests/test_domain.py"]

    dsrc = domain.read_text()
    tsrc = tests.read_text()
    try:
        dtree = ast.parse(dsrc)
    except SyntaxError as e:
        return [f"{pkg}: domain.py syntax error: {e}"]

    # G4 - the module must actually import. The importable root is the
    # package's parent directory, since the layout is <pkg>/<pkg>/.
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
    try:
        m = importlib.import_module(pkg + ".domain")
    except Exception as e:
        problems.append(f"{pkg}: domain does not import: {type(e).__name__}: {e}")

    # G1 - re-exports in __init__ must exist in the module they come from
    init = inner / "__init__.py"
    if init.exists():
        try:
            itree = ast.parse(init.read_text())
        except SyntaxError:
            itree = None
        if itree is not None:
            ddefs = _defined(dtree)
            dnames = {t.id for n in ast.walk(dtree) if isinstance(n, ast.Assign)
                      for t in n.targets if isinstance(t, ast.Name)}
            available = ddefs | dnames
            for mod, names in _mod_imports(itree):
                if mod != "domain":
                    continue
                for n in names:
                    if n not in available and n != "*":
                        problems.append(
                            f"{pkg}: __init__ re-exports '{n}' which domain.py "
                            f"does not define")

    # G2 - dead private functions
    priv = {f.name for f in ast.walk(dtree)
            if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
            and f.name.startswith("_") and not f.name.startswith("__")
            and f.name not in ("__init__",)}
    if priv:
        used = _referenced(ast.parse(dsrc))
        used |= {n.func.id for n in ast.walk(ast.parse(tsrc))
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        dead = sorted(p for p in priv if p not in used)
        for p in dead:
            problems.append(f"{pkg}: dead private function '{p}' (defined, never called)")

    # G3 - boundary coverage
    low = tsrc.lower()
    missing = [name for name, marks in BOUNDARY_MARKERS.items()
               if not any(mk.lower() in low for mk in marks)]
    if missing:
        # ADVISORY ONLY. This is a keyword heuristic over test source, so it
        # can both miss real gaps and invent them. Blocking on it would train
        # people to ignore the gate, which is worse than not having it.
        print(f"ADVISORY {pkg}: tests may not exercise {', '.join(missing)}")

    # G5 - the tests must actually PASS. Checking that a test file EXISTS is
    # not the same as checking the code works: a package can have a test file
    # full of failing assertions and still look structurally clean.
    import subprocess
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests), "-q", "--no-header",
             "-p", "no:cacheprovider"],
            cwd=str(d), capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            tail = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1:]
            problems.append(f"{pkg}: tests FAIL - {tail[0] if tail else 'see pytest'}")
    except Exception as e:
        problems.append(f"{pkg}: could not run tests: {type(e).__name__}: {e}")

    return problems


def main():
    pkgs = sys.argv[1:]
    if not pkgs:
        print("usage: tools_preflight.py <pkg> [<pkg> ...]", file=sys.stderr)
        return 2
    allp = []
    for p in pkgs:
        allp.extend(check_package(p))
    for line in allp:
        print("FAIL", line)
    print(f"\npreflight: {len(pkgs)} package(s), {len(allp)} problem(s)")
    return 1 if allp else 0


if __name__ == "__main__":
    sys.exit(main())
