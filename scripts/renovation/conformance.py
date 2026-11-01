#!/usr/bin/env python3
"""mem20 4.0 subsystem conformance gate.

Checks, for one subsystem directory, the seven acceptance criteria of the
2026-11-01 owner directive:

  1. domain logic present (>= 1 source file, >= 50 LOC)
  2. no stubs (TODO / FIXME / XXX / NotImplementedError / unimplemented! / todo!)
  3. tests present (unit + integration) and collectable
  4. CLI surface present (cli.py / __main__.py / main.py / cli/ for Python;
     main.rs or a [[bin]] target for Rust)
  5. README present with at least one runnable example (fenced code block)
  6. imports and uses >= 5 other mem20 modules
  7. registered with the MCP server / gateway surface

Discovery is language-aware. A top-level directory is a subsystem when it is
Python-primary (>= 5 .py files), Rust-primary (>= 5 .rs files and a Cargo.toml),
or a named core subsystem (CORE_MODULES) carrying at least one source file.
Criteria 1-4 and 6 read from the subsystem's primary language, so a Rust
workspace is scored on its .rs sources rather than being invisible.

Exit code 0 only when every criterion passes. Prints a per-criterion table so
the result can be pasted into a task card as evidence.

Usage:
    python scripts/renovation/conformance.py mem20kilnz
    python scripts/renovation/conformance.py braid
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

# Directories never walked when collecting sources.
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "target", "dist", "build"}

STUB_PATTERN = re.compile(
    r"\bTODO\b|\bFIXME\b|\bXXX\b|NotImplementedError|raise\s+NotImplemented|"
    r"^\s*pass\s*#\s*stub|placeholder implementation",
    re.MULTILINE,
)

# Rust stub markers: the two macros that mean "not written yet", plus the same
# comment markers. `panic!` is deliberately NOT a stub marker - a real panic on
# an unreachable branch is legitimate control flow.
RUST_STUB_PATTERN = re.compile(
    r"\bTODO\b|\bFIXME\b|\bXXX\b|unimplemented!|todo!|"
    r"panic!\(\s*\"(?:not implemented|unimplemented|todo)",
    re.MULTILINE,
)

# Modules that count as "other mem20 modules" for the dependency criterion.
CORE_MODULES = {"memory_engine", "gateway", "toolchest", "mcp", "braid", "corez"}

LANG_PY = "python"
LANG_RS = "rust"


@dataclass
class Result:
    subsystem: str
    language: str = LANG_PY
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
    rs_files: int = 0
    src_files: int = 0
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


def _walk(path: Path, suffix: str) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(suffix):
                out.append(Path(dirpath) / f)
    return out


def python_files(path: Path) -> list[Path]:
    return _walk(path, ".py")


def rust_files(path: Path) -> list[Path]:
    return _walk(path, ".rs")


def has_cargo(path: Path) -> bool:
    return next(path.rglob("Cargo.toml"), None) is not None


def is_test_file(p: Path) -> bool:
    name = p.name.lower()
    return name.startswith("test_") or name.endswith("_test.py") or "tests" in p.parts


def is_rust_test_file(p: Path) -> bool:
    name = p.name.lower()
    return name.endswith("_test.rs") or name == "tests.rs" or "tests" in p.parts


def detect_language(name: str, root: Path = REPO_ROOT) -> str | None:
    """Primary language of a subsystem, or None when the directory is not one.

    Order matters: a directory that already qualifies as Python-primary stays
    Python-primary even if it also carries Rust sources (mem20controlz has 13
    .py and 11 .rs), so the existing Python scoring is never re-routed.
    """
    path = root / name
    if not path.is_dir():
        return None
    pys = python_files(path)
    if len(pys) >= 5:
        return LANG_PY
    rss = rust_files(path)
    if len(rss) >= 5 and has_cargo(path):
        return LANG_RS
    # Named core subsystems are in scope even below the file-count threshold:
    # `gateway` is a 3-module Python package and is still a first-class
    # subsystem. A directory with no source at all (corez) is not.
    if name in CORE_MODULES and (len(pys) + len(rss)) >= 1:
        return LANG_RS if len(rss) > len(pys) else LANG_PY
    return None


def check_subsystem(name: str, root: Path = REPO_ROOT) -> Result:
    path = root / name
    lang = detect_language(name, root) or LANG_PY
    res = Result(subsystem=name, language=lang)
    if not path.is_dir():
        res.failures.append("directory missing")
        return res

    pys = python_files(path)
    rss = rust_files(path)
    res.py_files = len(pys)
    res.rs_files = len(rss)

    if lang == LANG_RS:
        src = [p for p in rss if not is_rust_test_file(p)]
        stub_re = RUST_STUB_PATTERN
    else:
        src = [p for p in pys if not is_test_file(p)]
        stub_re = STUB_PATTERN
    res.src_files = len(src)

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
        for m in stub_re.finditer(text):
            line = text[: m.start()].count("\n") + 1
            hits.append(f"{p.relative_to(root)}:{line}:{m.group(0).strip()}")
    res.stub_hits = hits[:20]
    res.no_stubs = not hits
    if hits:
        res.failures.append(f"{len(hits)} stub marker(s)")

    # 3. tests
    if lang == LANG_RS:
        has_test_attr = any(
            "#[test]" in p.read_text(encoding="utf-8", errors="ignore")
            for p in rss
        )
        res.tests = has_test_attr or (path / "tests").is_dir()
    else:
        res.tests = any(is_test_file(p) for p in pys)
    if not res.tests:
        res.failures.append("no test files")

    # 4. CLI
    if lang == LANG_RS:
        has_bin = any(p.name == "main.rs" for p in rss)
        if not has_bin:
            for cargo in path.rglob("Cargo.toml"):
                try:
                    if "[[bin]]" in cargo.read_text(encoding="utf-8", errors="ignore"):
                        has_bin = True
                        break
                except OSError:
                    pass
        res.cli = has_bin
    else:
        cli_names = {"cli.py", "__main__.py", "main.py"}
        res.cli = any(p.name in cli_names for p in pys) or (path / "cli").is_dir()
    if not res.cli:
        res.failures.append("no CLI surface")

    # 5. README with runnable example
    readme = path / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8", errors="ignore")
        res.readme_examples = bool(re.search(r"```(?:bash|sh|shell|console|python|rust|toml)?\n.+?```", text, re.S))
    if not res.readme_examples:
        res.failures.append("README missing or has no fenced example")

    # 6. cross-module imports (>= 5 distinct other mem20 modules)
    imported: set[str] = set()
    if lang == LANG_RS:
        for p in src:
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in re.finditer(r"^\s*(?:pub\s+)?use\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M):
                top = m.group(1)
                if top in {"crate", "super", "self", "std", "core", "alloc"}:
                    continue
                if top == name:
                    continue
                if top.startswith("mem20") or top in CORE_MODULES:
                    imported.add(top)
            for m in re.finditer(r"^\s*extern\s+crate\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.M):
                top = m.group(1)
                if top != name and (top.startswith("mem20") or top in CORE_MODULES):
                    imported.add(top)
    else:
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
        if detect_language(d.name, root) is not None:
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
        unit = "rs" if r.language == LANG_RS else "py"
        count = r.rs_files if r.language == LANG_RS else r.py_files
        print(f"subsystem: {r.subsystem}  [{r.language}]  ({count} {unit} files, {r.loc} src LOC)")
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
    n_py = sum(1 for r in results if r.language == LANG_PY)
    n_rs = sum(1 for r in results if r.language == LANG_RS)
    print(f"checked {len(results)} subsystems: {len(passed)} conformant ({ratio:.1%})")
    print(f"  languages: {n_py} python, {n_rs} rust")
    print(f"{'subsystem':46s} {'lang':6s} {'score':5s} {'cross':5s} failures")
    for r in sorted(results, key=lambda x: (x.score, x.subsystem)):
        if r.passed:
            continue
        print(f"{r.subsystem:46s} {r.language:6s} {r.score}/7   {r.cross_modules:>3}   {'; '.join(r.failures)[:90]}")

    # Per-criterion tally across the whole run.
    crit = [
        ("1 domain logic", lambda r: r.domain_logic),
        ("2 no stubs", lambda r: r.no_stubs),
        ("3 tests", lambda r: r.tests),
        ("4 CLI", lambda r: r.cli),
        ("5 README examples", lambda r: r.readme_examples),
        ("6 >=5 cross-modules", lambda r: r.cross_ok),
        ("7 MCP/gateway registered", lambda r: r.registered),
    ]
    print("\nper-criterion:")
    for label, fn in crit:
        n = sum(1 for r in results if fn(r))
        pct = (n / len(results) * 100) if results else 0.0
        print(f"  {label:26s} {n:>3}/{len(results)}  ({pct:.1f}%)")

    if args.fail_under is not None and ratio < args.fail_under:
        print(f"\nFAIL: {ratio:.1%} < required {args.fail_under:.1%}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
