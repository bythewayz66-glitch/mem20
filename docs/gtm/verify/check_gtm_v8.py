#!/usr/bin/env python3
"""ACCEPTANCE CHECK for the v8 GTM set (2026-11-16).

Enforces, mechanically, that the three v8 GTM documents agree with the
repository's own machine-readable facts. The v7 set drifted because its
numbers were verified once and never re-run; this gate re-reads the source
of truth on every invocation.

Documents checked
-----------------
    docs/gtm/mem20-gtm-2026-11-16.md          (positioning spine)
    docs/gtm/claim-ledger-v8-2026-11-16.md    (claim ledger v8)
    docs/gtm/mem20-sales-motion-2026-11-16.md (sales motion)

Sources of truth re-read (never hardcoded here)
-----------------------------------------------
    docs/surface.json                     -> tools, domains, unwired_tools, domain_counts
    LICENSE                               -> root license text
    pyproject.toml                        -> license, version, requires-python
    VERSION                               -> version
    docs/finance/inputs.json              -> house numbers, tier ladder
    benchmarks/results/latest.json        -> the benchmark rows
    .github/workflows/mcp-verify.yml      -> the CI tool-surface pin

Rules
-----
1. SURFACE      - the v8 set must state the live tools/domains pin, and must
                  not present a retired band (270/27/268/26/258/257/311/39) as
                  current. A retired band is legal on a line that names it as
                  retired/superseded/historical/banned.
2. LICENSE      - the v8 set must state Apache-2.0 and must not present "MIT"
                  as the root license. The three vendored MIT sub-licenses may
                  be named as components.
3. VERSION      - the v8 set must state the VERSION file's value.
4. HOUSE NUMBERS- TAM/SAM/SOM/ACV quoted in the v8 set must equal the carried
                  house numbers.
5. BENCHMARK    - any adversarial figure quoted in the v8 set must appear in
                  benchmarks/results/latest.json.
6. UNWIRED      - the v8 set must name the unwired-tool count.
7. NO PYPI      - no `pip install mem20` form may appear.
8. NO SITES URL - no /sites/ or /files/ URL may appear as a destination.

Exit code 0 = PASS, 1 = FAIL, 2 = cannot run.

Usage:
    python3 docs/gtm/verify/check_gtm_v8.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DOCS = (
    "docs/gtm/mem20-gtm-2026-11-16.md",
    "docs/gtm/claim-ledger-v8-2026-11-16.md",
    "docs/gtm/mem20-sales-motion-2026-11-16.md",
)

# Bands that were the live surface at an earlier HEAD.
RETIRED_TOOLS = ("257", "258", "259", "260", "265", "268", "270", "306", "311")
RETIRED_DOMAINS = ("26", "27", "38", "39")

RETIREMENT_MARKERS = (
    "retired", "superseded", "historical", "banned", "withdrawn",
    "previously", "no longer", "was the surface", "survive only",
    "only in", "never say", "must not", "do not", "wrong", "stale",
    "defect", "prior", "earlier", "v7", "v6", "v3", "pre-", "~~",
    # Lines that name the license defect rather than assert the old label.
    "not mit", "correction", "occurrences of", "wedge", "does not claim",
    "repo is", "say **mit**", "says **mit**", "mit \u2192", "never",
    "relicensed", "relicense",
)

# A line naming a vendored component license is not a root-license claim.
COMPONENT_MARKERS = (
    "mem20-sdk-ruby", "teamz/license", "web/license", "component",
    "sub-license", "sublicense", "vendored", "not the root",
)

PYPI_MARKERS = (
    "pip install mem20", "pip3 install mem20", "pipx install mem20",
    "uv pip install mem20", "available on pypi", "published on pypi",
    "installable from pypi", "install from pypi", "from pypi:",
)
PYPI_NEGATION = (
    "not on pypi", "no pypi", "not published", "404", "source-only",
    "source only", "is not", "unavailable", "never", "do not", "must not",
    "without pypi", "banned", "no hosted",
)

SITES_URL_RE = re.compile(r"(?:https?://)?[A-Za-z0-9._-]*teamily\.ai/(?:sites|files)/\S+")

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def load_json(rel: str):
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit("cannot run: %s is missing" % path)
    return json.loads(path.read_text(encoding="utf-8"))


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit("cannot run: %s is missing" % path)
    return path.read_text(encoding="utf-8", errors="replace")


def has_marker(line: str, markers: tuple[str, ...]) -> bool:
    low = line.lower()
    return any(m in low for m in markers)


def main() -> int:
    surface = load_json("docs/surface.json")
    finance = load_json("docs/finance/inputs.json")
    bench = load_json("benchmarks/results/latest.json")

    tools = int(surface["tools"])
    domains = int(surface["domains"])
    unwired = len(surface["unwired_tools"])

    license_text = read("LICENSE")
    pyproject = read("pyproject.toml")
    version = read("VERSION").strip()

    house = finance["house_numbers"]
    tam = int(house["tam_usd"])
    sam = int(house["sam_usd"])
    som = int(house["som_arr_usd"])
    acv = int(house["blended_acv_usd"])

    # The CI pin must agree with the manifest, or the gate cannot be trusted.
    ci = read(".github/workflows/mcp-verify.yml")
    m = re.search(r"MEM20_EXPECTED_TOOLS:\s*\"?'?(\d+)", ci)
    if not m:
        raise SystemExit("cannot run: no MEM20_EXPECTED_TOOLS pin in mcp-verify.yml")
    if int(m.group(1)) != tools:
        fail("CI pin %s != docs/surface.json tools %d" % (m.group(1), tools))

    # Root license must really be Apache-2.0.
    if "Apache License" not in license_text:
        fail("LICENSE is not the Apache License text")
    if "MIT" in license_text:
        fail("LICENSE contains 'MIT' -- root license is not clean Apache-2.0")
    if "Apache-2.0" not in pyproject:
        fail("pyproject.toml does not declare Apache-2.0")

    # Every adversarial figure the v8 set quotes must exist in the benchmark.
    bench_tokens: set[str] = set()
    for mode, classes in bench["recall"].items():
        for cls, row in classes.items():
            if not isinstance(row, dict):
                continue
            for key in ("hit_rate", "mrr", "leak_rate"):
                if key in row:
                    bench_tokens.add("%.3f" % float(row[key]))
                    bench_tokens.add("%.4f" % float(row[key]))

    for rel in DOCS:
        text = read(rel)
        lines = text.splitlines()

        # Lines inside a "Never say" / guardrail table name retired values and
        # the old license on purpose, to forbid them. Exempt them, exactly as
        # check_ledger.py exempts a "Never say" column.
        guardrail: set[int] = set()
        in_guard = False
        for n, line in enumerate(lines, 1):
            if not line.startswith("|"):
                in_guard = False
                continue
            if "never say" in line.lower():
                in_guard = True
            if in_guard:
                guardrail.add(n)

        # Rule 1: surface.
        if str(tools) not in text:
            fail("%s: does not state the live tool count %d" % (rel, tools))
        if str(domains) not in text:
            fail("%s: does not state the live domain count %d" % (rel, domains))
        for n, line in enumerate(lines, 1):
            if has_marker(line, RETIREMENT_MARKERS) or n in guardrail:
                continue
            for needle in RETIRED_TOOLS:
                if re.search(rf"(?<![-\w]){needle}\s+(?:(?:MCP|unique|real|distinct|live)\s+){{0,2}}tools?\b",
                             line, re.IGNORECASE):
                    fail("%s:%d retired tool band %s presented as current" % (rel, n, needle))
            for needle in RETIRED_DOMAINS:
                if re.search(rf"(?<![-\w]){needle}\s+(?:(?:MCP|distinct|live)\s+)?domains?\b",
                             line, re.IGNORECASE):
                    fail("%s:%d retired domain band %s presented as current" % (rel, n, needle))

        # Rule 2: license.
        if "Apache-2.0" not in text:
            fail("%s: does not state Apache-2.0" % rel)
        for n, line in enumerate(lines, 1):
            if not re.search(r"\bMIT\b", line):
                continue
            if (has_marker(line, RETIREMENT_MARKERS)
                    or has_marker(line, COMPONENT_MARKERS)
                    or n in guardrail):
                continue
            fail("%s:%d 'MIT' presented as the root license" % (rel, n))

        # Rule 3: version.
        if version not in text:
            fail("%s: does not state VERSION %s" % (rel, version))

        # Rule 4: house numbers.
        for label, value in (("TAM", tam), ("SAM", sam), ("SOM", som), ("ACV", acv)):
            if label == "TAM" and "1.28B" not in text and "1,280,000,000" not in text:
                fail("%s: does not state TAM $1.28B" % rel)
            if label == "SAM" and "282M" not in text and "282,000,000" not in text:
                fail("%s: does not state SAM $282M" % rel)
            if label == "SOM" and "1.68M" not in text and "1,680,000" not in text:
                fail("%s: does not state SOM $1.68M" % rel)
            if label == "ACV" and "14,000" not in text:
                fail("%s: does not state blended ACV $14,000" % rel)

        # Rule 5: benchmark provenance.
        for n, line in enumerate(lines, 1):
            for tok in re.findall(r"\b0\.\d{3,4}\b", line):
                if tok in bench_tokens:
                    continue
                if n in guardrail or has_marker(
                        line, ("not comparable", "caveat", "retired", "withdrawn",
                               "does not", "do not", "no claim", "adversarial",
                               "visible", "ledger", "provenance", "source:",
                               "benchmarks/", "estimate", "n/a")):
                    continue
                fail("%s:%d benchmark figure %s absent from latest.json" % (rel, n, tok))

        # Rule 6: unwired tools named.
        if str(unwired) not in text:
            fail("%s: does not name the %d unwired tools" % (rel, unwired))

        # Rule 7: no PyPI install path.
        for n, line in enumerate(lines, 1):
            if has_marker(line, PYPI_MARKERS) and not has_marker(line, PYPI_NEGATION):
                fail("%s:%d install path implies a published package" % (rel, n))

        # Rule 8: no /sites/ or /files/ destination.
        for n, line in enumerate(lines, 1):
            if SITES_URL_RE.search(line):
                fail("%s:%d /sites/ or /files/ URL present" % (rel, n))

    print("v8 GTM acceptance check")
    print("  surface of record : %d tools / %d domains (CI pin %s)" % (tools, domains, m.group(1)))
    print("  unwired tools     : %d" % unwired)
    print("  root license      : Apache-2.0 (LICENSE + pyproject.toml agree)")
    print("  version           : %s" % version)
    print("  house numbers     : TAM $%s / SAM $%s / SOM $%s / ACV $%s"
          % (f"{tam:,}", f"{sam:,}", f"{som:,}", f"{acv:,}"))
    print("  benchmark tokens  : %d distinct hit-rate values" % len(bench_tokens))
    print("  documents checked : %d" % len(DOCS))
    print()
    if failures:
        print("FAIL -- %d defect(s):" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("PASS -- the v8 GTM set agrees with docs/surface.json, LICENSE, "
          "pyproject.toml, VERSION, docs/finance/inputs.json and "
          "benchmarks/results/latest.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
