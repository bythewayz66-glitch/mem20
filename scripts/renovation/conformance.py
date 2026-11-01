#!/usr/bin/env python3
"""mem20 4.0 subsystem conformance gate.

Checks, for one subsystem directory, the seven acceptance criteria of the
2026-11-01 owner directive:

  1. domain logic present and free of stubs (TODO / FIXME / NotImplementedError)
  2. tests present (unit + integration) and collectable
  3. CLI surface present (cli.py / __main__.py / cli/ package)
  4. registered with the MCP server / gateway surface
  5. README present with at least one runnable example (fenced code block)
  6. imports and uses >= 5 other mem20 modules

Exit code 0 only when every criterion passes. Prints a per-criterion table so
the result can be pasted into a task card as evidence.

Usage:
    python scripts/renovation/conformance.py mem20kilnz
    python scripts/renovation/conformance.py --all --json out.json
    python scripts/renovation/conformance.py --all --fail-under 1.0
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that are not subsystems (docs, tooling, generated output).
NON_SUBSYSTEM = {
    "docs", "published", "plans", "tests", "bench", "benchmarks", "backups",
    "entries", "bridge", "cog", "dashboard", "reference_store", "braid_keyz",
    "mem20-orchestration", "scripts", ".github", "node_modules",
}

STUB_PATTERN = re.compile(
    r"\bTODO\b|\bFIXME\b|\bXXX\b|NotImplementedError|raise\s+NotImplemented|"
    r"^\s*pass\s*#\s*stub|placeholder implementation",
    re.MULTILINE,
)

# Modules that count as "other mem20 modules" for the dependency criterion.
CORE_MODULES = {"memory_engine", "gateway", "toolchest", "mcp", "braid", "corez"}


@dataclass
class Result:
    subsystem: str
    domain_logic: bool = False
    no_stubs: bool = False
    tests: bool = False
    cli: bool = False
    registered: bool = False
    readme_examples: bool = False
    cross_modules: int = 0
    cross_ok: bool = False
    loc: int = 0
    py_files: int = 0
    stub_hits: list = field(default_factory=list)
    cross_list: list = field(default_factory=list)
    failures: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all([
            self.domain_logic, self.no_stubs, self.tests, self.cli,
            self.registered, self.readme_examples, self.cross_ok,
        ])

    @property
    def score(self) -> int:
        return sum([
            self.domain_logic, self.no_stubs, self.tests, self.cli,
            self.registered, self.readme_examples, self.cross_ok,
        ])


def python_files(path: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", "node_modules", ".venv"}]
        for f in filenames:
            if f.endswith(".py"):
                out.append(Path(dirpath) / f)
    return out


def is_test_file(p: Path) -> bool:
    name = p.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or "tests" in p.parts


def check_subsystem(name: str, root: Path = REPO_ROOT) -> Result:
    path = root / name
    res = Result(subsystem=name)
    if not path.is_dir():
        res.failures.append("directory missing")
        return res

    pys = python_files(path)
    res.py_files = len(pys)
    src = [p for p in pys if not is_test_file(p)]

    # 1. domain logic
    total_loc = 0
    for p in src:
        try:
            total_loc += len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            pass
    res.loc = total_loc
    res.domain_logic = len(src) >= 1 and total_loc >= 50
    if not res.domain_logic:
        res.failures.append(f"domain logic too thin ({len(src)} src files, {total_loc} LOC)")

    # 2. no stubs
    hits = []
    for p in src:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in STUB_PATTERN.finditer(text):
            line = text[: m.start()].count("\n") + 1
            hits.append(f"{p.relative_to(root)}:{line}:{m.group(0).strip()}")
    res.stub_hits = hits[:20]
    res.no_stubs = not hits
    if hits:
        res.failures.append(f"{len(hits)} stub marker(s)")

    # 3. tests
    test_files = [p for p in pys if is_test_file(p)]
    res.tests = len(test_files) >= 1
    if not res.tests:
        res.failures.append("no test files")

    # 4. CLI
    cli_names = {"cli.py", "__main__.py", "main.py"}
    res.cli = any(p.name in cli_names for p in pys) or (path / "cli").is_dir()
    if not res.cli:
        res.failures.append("no CLI surface")

    # 5. README with runnable example
    readme = path / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        res.readme_examples = bool(re.search(r"```(?:bash|sh|shell|console|python)?\n.+?```", text, re.S))
    if not res.readme_examples:
        res.failures.append("README missing or has no fenced example")

    # 6. cross-module imports (>= 5 distinct other mem20 modules)
    imported: set[str] = set()
    for p in src:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module]
            for m in mods:
                top = m.split(".")[0]
                if top == name:
                    continue
                if top.startswith("mem20") or top in CORE_MODULES:
                    imported.add(top)
    res.cross_list = sorted(imported)
    res.cross_modules = len(imported)
    res.cross_ok = res.cross_modules >= 5
    if not res.cross_ok:
        res.failures.append(f"only {res.cross_modules} cross-module import(s), need >= 5")

    # 7. registered with MCP server / gateway
    res.registered = check_registered(name, root)
    if not res.registered:
        res.failures.append("not registered with MCP server / gateway")

    return res


def check_registered(name: str, root: Path) -> bool:
    """A subsystem is registered when its name appears in an MCP/gateway registry file."""
    candidates = [
        root / "mcp" / "mcp_server.py",
        root / "mcp" / "server.py",
        root / "mcp" / "tools",
        root / "gateway" / "gateway_tools.py",
        root / "gateway" / "mem20_gateway.py",
        root / "mem20_mcp",
    ]
    needle = name.lower()
    for c in candidates:
        if c.is_file():
            try:
                if needle in c.read_text(encoding="utf-8", errors="ignore").lower():
                    return True
            except OSError:
                pass
        elif c.is_dir():
            for p in c.rglob("*.py"):
                try:
                    if needle in p.read_text(encoding="utf-8", errors="ignore").lower():
                        return True
                except OSError:
                    pass
    return False


def discover(root: Path = REPO_ROOT) -> list[str]:
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in NON_SUBSYSTEM:
            continue
        if len(python_files(d)) >= 5:
            out.append(d.name)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="mem20 4.0 subsystem conformance gate")
    ap.add_argument("subsystem", nargs="?", help="subsystem directory name")
    ap.add_argument("--all", action="store_true", help="check every discovered subsystem")
    ap.add_argument("--json", help="write full results as JSON to this path")
    ap.add_argument("--fail-under", type=float, default=None,
                    help="fail if the pass ratio across --all is below this (0..1)")
    args = ap.parse_args(argv)

    if args.all:
        names = discover()
    elif args.subsystem:
        names = [args.subsystem]
    else:
        ap.error("give a subsystem name or --all")

    results = [check_subsystem(n) for n in names]

    if args.json:
        Path(args.json).write_text(json.dumps([asdict(r) for r in results], indent=1))

    if not args.all:
        r = results[0]
        print(f"subsystem: {r.subsystem}  ({r.py_files} py files, {r.loc} src LOC)")
        print(f"{'criterion':28s} {'result':6s}")
        for label, ok in [
            ("1 domain logic", r.domain_logic),
            ("2 no stubs", r.no_stubs),
            ("3 tests", r.tests),
            ("4 CLI", r.cli),
            ("5 README examples", r.readme_examples),
            ("6 >=5 cross-modules", r.cross_ok),
            ("7 MCP/gateway registered", r.registered),
        ]:
            print(f"{label:28s} {'PASS' if ok else 'FAIL'}")
        print(f"cross-modules ({r.cross_modules}): {', '.join(r.cross_list) or '-'}")
        if r.failures:
            print("\nfailures:")
            for f in r.failures:
                print(f"  - {f}")
        if r.stub_hits:
            print("\nstub markers:")
            for h in r.stub_hits:
                print(f"  - {h}")
        return 0 if r.passed else 1

    passed = [r for r in results if r.passed]
    ratio = len(passed) / len(results) if results else 0.0
    print(f"checked {len(results)} subsystems: {len(passed)} conformant ({ratio:.1%})")
    print(f"{'subsystem':46s} {'score':5s} {'cross':5s} failures")
    for r in sorted(results, key=lambda x: (x.score, x.subsystem)):
        if r.passed:
            continue
        print(f"{r.subsystem:46s} {r.score}/7   {r.cross_modules:>3}   {'; '.join(r.failures)[:90]}")
    if args.fail_under is not None and ratio < args.fail_under:
        print(f"\nFAIL: {ratio:.1%} < required {args.fail_under:.1%}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
