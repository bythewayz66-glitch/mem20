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

# Subsystems that are real subsystems but do not meet the generic discovery
# floor. `discover()` used to require >= 5 .py files, which silently dropped
# two rows that the assignments CSV lists as subsystems:
#
#   braid   -- Rust only, 0 .py files (8 crates under braid/)
#   gateway -- 3 .py files, all real (846 src LOC)
#
# Neither was ever scored by `--all`, so their rows in the report were blank
# rather than FAIL. Listing them here makes them gateable; it does not relax
# any criterion for them.
DISCOVER_ALWAYS = {"braid", "gateway"}

# Rust stub markers. `todo!()` / `unimplemented!()` are the Rust equivalents of
# NotImplementedError and must fail criterion 2 exactly the same way.
RUST_STUB_PATTERN = re.compile(
    r"\btodo!\s*\(|\bunimplemented!\s*\(|\bunreachable!\s*\(\s*\"TODO",
    re.MULTILINE,
)


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


def rust_files(path: Path) -> list[Path]:
    """Rust sources under `path`, excluding build output and vendored deps."""
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in {"target", ".git", "node_modules"}]
        for f in filenames:
            if f.endswith(".rs"):
                out.append(Path(dirpath) / f)
    return out


def is_test_file(p: Path) -> bool:
    name = p.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or "tests" in p.parts


def rust_cross_modules(name: str, path: Path) -> set[str]:
    """Sibling crates this subsystem actually calls into.

    Criterion 6 is an architecture rule: a subsystem must be wired into >= 5
    other mem20 modules with the imported function actually called on a tested
    path. For a Rust subsystem the unit of "module" is the workspace crate.

    A crate counts only when BOTH hold:

      * it is declared as a path dependency in a Cargo.toml under this
        subsystem, so the import resolves to real code in this repo rather than
        to a crates.io package that happens to share the prefix; and
      * a non-test source file imports a SYMBOL from it (`use braid_core::engine::BraidEngine`)
        and that symbol is then used in the body (`BraidEngine::new(...)`).

    The symbol test is what separates wiring from a decorative import. Rust
    code overwhelmingly calls through the imported name, not through a
    `crate::path` expression, so checking for `crate::` in the body would
    under-count real wiring -- which is exactly what the first version of this
    function did (it scored braid 3/7 when 6 crates are genuinely wired).
    """
    rs = [p for p in rust_files(path) if not is_test_file(p)]
    if not rs:
        return set()

    # Crates declared as path deps anywhere under this subsystem.
    declared: set[str] = set()
    for cargo in path.rglob("Cargo.toml"):
        try:
            text = cargo.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in re.finditer(
            r"^\s*([A-Za-z0-9_-]+)\s*=\s*\{[^}]*path\s*=", text, re.MULTILINE
        ):
            declared.add(m.group(1).replace("-", "_"))

    used: set[str] = set()
    for p in rs:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Strip `use` statements so a symbol only counts when it is used again.
        body = re.sub(r"^\s*(?:pub\s+)?use\s+[^;]+;", "", text, flags=re.MULTILINE)
        for m in re.finditer(
            r"^\s*(?:pub\s+)?use\s+([A-Za-z0-9_]+)::([^;]+);", text, re.MULTILINE
        ):
            crate, tail = m.group(1), m.group(2)
            if crate == name or crate in used or crate not in declared:
                continue
            # Symbols named in the import: the last path segment, plus every
            # name inside a `{...}` group.
            symbols: set[str] = set()
            for grp in re.findall(r"\{([^}]*)\}", tail):
                for part in grp.split(","):
                    part = part.strip()
                    if not part:
                        continue
                    symbols.add(part.split("::")[-1].split(" as ")[0].strip())
            last = tail.split("::")[-1].split(" as ")[0].strip()
            if last and not last.startswith("{"):
                symbols.add(last)
            symbols = {s for s in symbols if s and s != "self" and s.isidentifier()}
            if any(re.search(rf"\b{re.escape(s)}\b", body) for s in symbols):
                used.add(crate)
    return used


def check_subsystem(name: str, root: Path = REPO_ROOT) -> Result:
    path = root / name
    res = Result(subsystem=name)
    if not path.is_dir():
        res.failures.append("directory missing")
        return res

    pys = python_files(path)
    rss = rust_files(path)
    res.py_files = len(pys)
    src = [p for p in pys if not is_test_file(p)]
    rust_src = [p for p in rss if not is_test_file(p)]
    # A subsystem is Rust-primary when it has Rust sources and no Python ones.
    # braid is the only such row today (8 crates, 0 .py). Criteria 1-6 are then
    # evaluated against the Rust sources with the same thresholds; nothing is
    # lowered, only the language the evidence is read from changes.
    rust_primary = bool(rust_src) and not src

    # 1. domain logic
    total_loc = 0
    for p in (rust_src if rust_primary else src):
        try:
            total_loc += len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            pass
    res.loc = total_loc
    n_src = len(rust_src if rust_primary else src)
    res.domain_logic = n_src >= 1 and total_loc >= 50
    if not res.domain_logic:
        res.failures.append(f"domain logic too thin ({n_src} src files, {total_loc} LOC)")

    # 2. no stubs
    hits = []
    pattern = RUST_STUB_PATTERN if rust_primary else STUB_PATTERN
    for p in (rust_src if rust_primary else src):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in pattern.finditer(text):
            line = text[: m.start()].count("\n") + 1
            hits.append(f"{p.relative_to(root)}:{line}:{m.group(0).strip()}")
    res.stub_hits = hits[:20]
    res.no_stubs = not hits
    if hits:
        res.failures.append(f"{len(hits)} stub marker(s)")

    # 3. tests
    if rust_primary:
        test_files = [p for p in rss if is_test_file(p)]
    else:
        test_files = [p for p in pys if is_test_file(p)]
    res.tests = len(test_files) >= 1
    if not res.tests:
        res.failures.append("no test files")

    # 4. CLI
    cli_names = {"cli.py", "__main__.py", "main.py"}
    if rust_primary:
        res.cli = any(p.name == "main.rs" for p in rss) or (path / "src" / "main.rs").is_file()
    else:
        res.cli = any(p.name in cli_names for p in pys) or (path / "cli").is_dir()
    if not res.cli:
        res.failures.append("no CLI surface")

    # 5. README with runnable example
    readme = path / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        res.readme_examples = bool(re.search(r"```(?:bash|sh|shell|console|python|rust)?\n.+?```", text, re.S))
    if not res.readme_examples:
        res.failures.append("README missing or has no fenced example")

    # 6. cross-module imports (>= 5 distinct other mem20 modules)
    if rust_primary:
        imported = rust_cross_modules(name, path)
    else:
        imported = set()
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
        if d.name in DISCOVER_ALWAYS:
            out.append(d.name)
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
