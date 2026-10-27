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
"""
import argparse
import ast
import json
import pathlib

# Modules whose stem does not name the domain its tools belong to.
DOMAIN_OVERRIDES = {
    "server": "job",
    "enhanced_memory": "memory",
}


def domain_for(path: pathlib.Path) -> str:
    stem = path.stem.replace("_tools", "")
    return DOMAIN_OVERRIDES.get(stem, stem)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="..", help="repo root containing mcp/")
    ap.add_argument("--out", default="src/data/tools.json")
    a = ap.parse_args()

    root = pathlib.Path(a.root) / "mcp"
    files = sorted(set(root.glob("tools/*.py")) | set(root.glob("*.py")))

    tools = {}
    for p in files:
        try:
            tree = ast.parse(p.read_text(errors="ignore"))
        except SyntaxError:
            continue
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
            tools[name.value] = {
                "n": name.value,
                "t": lit("title") or "",
                "d": lit("description") or "",
                "x": domain_for(p),
                "p": props,
            }

    domains = sorted({t["x"] for t in tools.values()})
    payload = {
        "source": "mcp/**/*.py AST extraction of mt.Tool registrations",
        "files_scanned": len(files),
        "count": len(tools),
        "domain_count": len(domains),
        "domains": domains,
        "tools": sorted(tools.values(), key=lambda t: t["n"]),
    }
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")))
    print(f"{len(files)} files -> {len(tools)} tools across {len(domains)} domains -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
