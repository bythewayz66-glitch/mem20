#!/usr/bin/env python3
"""Regenerate src/data/tools.json from the estate's own tool registrations.

Parses every module that registers tools for a `mt.Tool(name=, title=,
description=, inputSchema=)` call. No network, no imports, no execution of
tool code.

    python3 scripts/extract-tools.py --root .. --out src/data/tools.json

Scanned modules (the registry is NOT confined to mcp/tools/):
  mcp/tools/*.py   per-domain mixins (world, vcs, fs, db, cloud, ...)
  mcp/*.py         core mixins + server (memory 52, cognitive 19, roadmap 4,
                   job 2). These were missing from the first version of this
                   script, which reported 203 tools instead of 270.

Domain assignment: the owning module's stem, minus the `_tools` suffix. The
`server` module owns the job_* pair, so it folds into the `job` domain.
`enhanced_memory` and `memory` are one domain (Core memory) in the taxonomy,
so both fold into `memory`.

WIRING GATE (added 2026-11-01)
------------------------------
A `mt.Tool(...)` declaration is not a tool. It only becomes one if the mixin
class that declares it is actually inherited by `Mem20MCPServer` in
`mcp/server.py` — that inheritance is what runs `register_*_tools()` and
populates `self.tools`. Two modules (`eventstream_tools.py`,
`lattice_tools.py`, merged in PR #161) declared 10 tools whose mixins were
never added to the class bases, so the catalog advertised 282 tools while the
running server served 272. The catalog is the surface users trust, so it must
count what the server can actually answer, not what the source tree mentions.

This script therefore parses `mcp/server.py`, collects the base classes of
`Mem20MCPServer`, maps each mixin class to the module that defines it, and
counts only tools from wired modules. Orphaned declarations are reported on
stderr and in the payload's `unwired` field so the gap stays visible instead
of silently inflating the count.
"""
import argparse
import ast
import json
import pathlib
import sys

# Modules whose stem does not name the domain its tools belong to.
DOMAIN_OVERRIDES = {
    "server": "job",
    "enhanced_memory": "memory",
}

SERVER_MODULE = "server.py"
SERVER_CLASS = "Mem20MCPServer"


def domain_for(path: pathlib.Path) -> str:
    stem = path.stem.replace("_tools", "")
    return DOMAIN_OVERRIDES.get(stem, stem)


def wired_mixins(root: pathlib.Path) -> set:
    """Base-class names of Mem20MCPServer, i.e. the mixins that actually run."""
    server = root / SERVER_MODULE
    if not server.is_file():
        return set()
    try:
        tree = ast.parse(server.read_text(errors="ignore"))
    except SyntaxError:
        return set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == SERVER_CLASS:
            names = set()
            for base in node.bases:
                ident = getattr(base, "id", None) or getattr(base, "attr", None)
                if ident:
                    names.add(ident)
            return names
    return set()


def mixin_classes(tree: ast.AST) -> set:
    """Class names defined in a module that look like tool mixins."""
    return {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef) and n.name.endswith("Mixin")
    }


def installer_modules(root: pathlib.Path) -> set:
    """Module stems whose ``install()`` is called from ``mcp/tools/__init__.py``.

    Some subsystems attach their tools by monkeypatching an existing mixin's
    ``register_*_tools`` rather than by being inherited (RM-239, RM-052). The
    package ``__init__`` imports and calls each ``install()``, so those modules
    are wired even though their mixin never appears in the class bases.
    """
    init = root / "tools" / "__init__.py"
    if not init.is_file():
        return set()
    try:
        tree = ast.parse(init.read_text(errors="ignore"))
    except SyntaxError:
        return set()
    stems = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            # `from tools.rm239_tools import install as _install_rm239`
            if any(a.name == "install" for a in node.names):
                stems.add(node.module.split(".")[-1])
    return stems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..", help="repo root containing mcp/")
    ap.add_argument("--out", default="src/data/tools.json")
    a = ap.parse_args()

    root = pathlib.Path(a.root) / "mcp"
    files = sorted(set(root.glob("tools/*.py")) | set(root.glob("*.py")))

    wired = wired_mixins(root)
    if not wired:
        print(
            f"FATAL: could not read {SERVER_CLASS} bases from mcp/{SERVER_MODULE}; "
            "refusing to emit a catalog that is not wiring-checked.",
            file=sys.stderr,
        )
        return 2
    installed = installer_modules(root)

    tools = {}
    unwired = {}
    for p in files:
        try:
            tree = ast.parse(p.read_text(errors="ignore"))
        except SyntaxError:
            continue
        # A module contributes tools only if one of its mixins is inherited by
        # the server, or its install() is called from mcp/tools/__init__.py.
        # Modules with no mixin class at all (e.g. server.py, which registers
        # job_* directly) are always in scope.
        declared = mixin_classes(tree)
        is_wired = (
            (not declared)
            or bool(declared & wired)
            or p.stem in installed
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if fn != "Tool":
                continue
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            name = kw.get("name")
            if not isinstance(name, ast.Constant) or not isinstance(name.value, str):
                continue

            def lit(key):
                v = kw.get(key)
                if v is None:
                    return None
                try:
                    return ast.literal_eval(v)
                except Exception:
                    return None

            schema = lit("inputSchema") or {}
            props = list(schema.get("properties", {})) if isinstance(schema, dict) else []
            record = {
                "n": name.value,
                "t": lit("title") or "",
                "d": lit("description") or "",
                "x": domain_for(p),
                "p": props,
            }
            if is_wired:
                tools[name.value] = record
            else:
                unwired[name.value] = {**record, "mixin": sorted(declared)[0]}

    domains = sorted({t["x"] for t in tools.values()})
    payload = {
        "source": "mcp/**/*.py AST extraction of mt.Tool registrations, "
                  "filtered to mixins inherited by Mem20MCPServer",
        "files_scanned": len(files),
        "count": len(tools),
        "domain_count": len(domains),
        "domains": domains,
        "tools": sorted(tools.values(), key=lambda t: t["n"]),
        # Declared in source but unreachable at runtime. Kept in the payload so
        # the gap is auditable rather than invisible; never counted in `count`.
        "unwired": sorted(unwired.values(), key=lambda t: t["n"]),
    }
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"{len(files)} files -> {len(tools)} tools across {len(domains)} domains -> {out}")
    if unwired:
        print(
            f"WARNING: {len(unwired)} tool(s) declared but NOT wired into "
            f"{SERVER_CLASS} (excluded from count): "
            + ", ".join(sorted(unwired)),
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
