#!/usr/bin/env python3
"""Converge every mem20 frontend surface on the live tool surface: 270 tools / 27 domains.

# Canonical number

270 distinct tools across 27 domains, reproduced two independent ways:

  1. `grep -o 'self\.tools\["[a-z0-9_]*"\]' mcp/**/*.py | sort -u | wc -l` -> 270
     (272 raw registrations, 2 shadowed duplicates).
  2. `python3 web/scripts/extract-tools.py` (AST, mt.Tool calls) -> 270 / 27.

# Why 257/26 and 268/26 were wrong

The old number undercounted in exactly two places:
  * the `memory_*` row listed 49 and the surface registers 52  (+3)
  * the 10 `lie_*` tools were absent from every table              (+10)
257 + 3 + 10 = 270. Those 10 `lie_*` tools are the 27th domain.

# Pass 1 vs pass 2

Pass 1 rewrites the phrasings ("257 tools", "~258-260 tools", "26 domains").
Pass 2 rewrites the *bare* KPI forms ("<div class=v>257</div>", "257-tool wall",
"49 of 257") but only in PASS2_FILES, because a bare number is ambiguous in a
page that also contains geometry (widths, z-indexes, chart bounds).

# What this script deliberately does NOT touch

Append-only / dated records keep their historical numbers, because rewriting
them would falsify the record rather than correct it:

  CHANGELOG.md                  history of earlier reconciles
  published/daily-reports/*.md  dated ops logs
  docs/audit/*.md               dated audits
  **/*.patch, bench/optionc     captured diffs of past states
  "older docs quote 258-260"    sentences that describe the retired value

Run:  python3 scripts/sweep-tool-counts.py            # dry run
      python3 scripts/sweep-tool-counts.py --apply    # write
"""
import argparse
import pathlib
import re

TOOLS = "270"
DOMAINS = "27"

# ---------------------------------------------------------------- pass 1
RULES = [
    # "~258-260 tools" hedges collapse to the measured value
    (re.compile(r"~?258\s*[\u2013\u2014-]\s*260\s+tools", re.I), f"{TOOLS} tools"),
    (re.compile(r"~258\s+tools", re.I), f"{TOOLS} tools"),
    # combined phrases, assorted separators
    (re.compile(r"\b(?:257|258|259|260|265|268)\s+tools\s+(?:across|in|/|\u00b7)\s+26\s+domains", re.I),
     f"{TOOLS} tools across {DOMAINS} domains"),
    # bare tool counts
    (re.compile(r"\b(?:257|258|259|260|265|268)\s+tools\b", re.I), f"{TOOLS} tools"),
    # bare domain counts (incl. "26 documented domains", "26 domains")
    (re.compile(r"\b26\s+domains\b", re.I), f"{DOMAINS} domains"),
]

# Pages that explain the row-vs-domain discrepancy; adding the lie_* domain
# takes the prefix table from 29 rows to 30.
ROWS_PAGES = {
    "published/sites/54ed398d-fb07-44ff-be48-5093f770d802/webpages/mem20-market-research-v3/index.html",
    "published/sites/54ed398d-fb07-44ff-be48-5093f770d802/documents/mem20-market-research-v3/gabe-bundle/mem20-market-research-v3.html",
}
ROWS_RULES = [
    (re.compile(r"\b29 rows\b"), "30 rows"),
    (re.compile(r'"29 domains"'), '"30 domains"'),
    (re.compile(r"\b29 domains\b(?=[^<]*row count)"), "30 domains"),
]

# ---------------------------------------------------------------- pass 2
# Files whose bare numbers are always the tool count. Verified line by line:
# none of these contain a geometry/layout value of 257.
PASS2_FILES = {
    "published/sites/051e63be-1243-478f-927b-7a669e0da877/webpages/mem20-ux-research-findings/index.html",
    "published/sites/538c6667-b0b7-410b-934d-44a3c34973b4/webpages/mem20-design-research/index.html",
    "published/sites/538c6667-b0b7-410b-934d-44a3c34973b4/webpages/mem20-design-research/wireframes.html",
    "published/sites/54009941-ffda-4e50-9bd1-8d0b88585a8b/webpages/mem20-perl-sdk-docs-update/index.html",
    "published/sites/54ed398d-fb07-44ff-be48-5093f770d802/webpages/mem20-market-research-v3/index.html",
    "published/sites/54ed398d-fb07-44ff-be48-5093f770d802/documents/mem20-market-research-v3/gabe-bundle/mem20-market-research-v3.html",
    "published/sites/66161135-9dd3-4110-9d76-87b9e526a037/webpages/mem20-launch/index.html",
    "published/sites/6c283fdf-9619-4cca-902c-2828a8c99e03/webpages/mem20-finance-report/index.html",
    "published/sites/9d718206-64d5-4cae-8f66-1766262ad900/webpages/mem20-ux-v2/personas.html",
    "published/sites/a590cfd2-ecab-4d81-925e-90a4812cf601/documents/mem20-sdk-docs-publish-leg/mem20-cpp-sdk-docs.html",
    "published/sites/a590cfd2-ecab-4d81-925e-90a4812cf601/documents/mem20-sdk-docs-publish-leg/mem20-perl-sdk-docs.html",
    "published/sites/e1381e73-4302-48e1-9117-7781c261e46e/webpages/mem20-prototype/index.html",
    "published/sites/ea6393ed-90a6-4a42-b2f2-536e27a0a061/webpages/mem20-admin-ops-ledger/index.html",
    "published/sites/e877db1e-5554-4e11-ae3e-a8b37c4756f3/presentations/mem20-launch-deck/slide_01.html",
}

PASS2_RULES = [
    # the retired band, e.g. "257-260" in a claim table
    (re.compile(r"\b(?:257|258|259|260)\s*[\u2013\u2014-]\s*260\b"), TOOLS),
    # per-domain average: 270 / 27 == 10.0 exactly
    (re.compile(r"<b>9\.88</b>\s*\(257\s*\u00f7\s*26\)"), f"<b>10.0</b> ({TOOLS} \u00f7 {DOMAINS})"),
    (re.compile(r"\b9\.88\b\s*\(257\s*\u00f7\s*26\)"), f"10.0 ({TOOLS} \u00f7 {DOMAINS})"),
    # 257 / 26 written as a ratio
    (re.compile(r"/\s*26(?=</small>)"), f"/ {DOMAINS}"),
    (re.compile(r"\b257\s*\u00f7\s*26\b"), f"{TOOLS} \u00f7 {DOMAINS}"),
    # bare tool count
    (re.compile(r"\b257\b"), TOOLS),
    # domain count only where it is the domain count
    (re.compile(r"domains\s*:\s*26\b"), f"domains:{DOMAINS}"),
    (re.compile(r"\b26(?=\s*[-/]\s*(?:tool|domain))"), DOMAINS),
    (re.compile(r"\b26-domain\b"), f"{DOMAINS}-domain"),
]

# The memory_* count moved 49 -> 52 in the same reconcile (two modules register it).
PASS2_LITERALS = {
    "published/sites/e1381e73-4302-48e1-9117-7781c261e46e/webpages/mem20-prototype/index.html": [
        ("49 of 257", f"52 of {TOOLS}"),
        ("<b>49</b> of <b>257</b>", f"<b>52</b> of <b>{TOOLS}</b>"),
        ("49 memory_* of 257", f"52 memory_* of {TOOLS}"),
        ("memoryTools:49", "memoryTools:52"),
        ("Memory tools <b>49</b>", "Memory tools <b>52</b>"),
        ("(49 memory_* of 270)", f"(52 memory_* of {TOOLS})"),
    ],
}

SKIP_DIRS = {".git", "node_modules", "dist", "build"}
SKIP_FILES = {
    "CHANGELOG.md",
    "bench/optionc/optionc.patch",
    # the shell says the count it stands behind out loud; CATALOG.count drives it
    "web/src/views/DocsFaq.tsx",
}
SKIP_PREFIXES = (
    "published/daily-reports/",
    "docs/audit/",
)
# Frontend surfaces only. Prose docs (README, docs/*.md) were reconciled by the
# docs leg and are outside this slice.
TEXT_EXT = {".html", ".htm", ".js", ".jsx", ".ts", ".tsx", ".css", ".vue", ".json"}


def skipped(rel: str) -> bool:
    if rel in SKIP_FILES:
        return True
    if rel.startswith(SKIP_PREFIXES):
        return True
    if rel.endswith(".patch"):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    root = pathlib.Path(a.root).resolve()
    changed_files = 0
    changed_lines = 0

    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in TEXT_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        if skipped(rel):
            continue

        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        out = text
        for pat, repl in RULES:
            out = pat.sub(repl, out)
        if rel in ROWS_PAGES:
            for pat, repl in ROWS_RULES:
                out = pat.sub(repl, out)
        if rel in PASS2_FILES:
            for old, new in PASS2_LITERALS.get(rel, []):
                out = out.replace(old, new)
            for pat, repl in PASS2_RULES:
                out = pat.sub(repl, out)

        if out == text:
            continue

        diffs = []
        for i, (old, new) in enumerate(zip(text.splitlines(), out.splitlines()), 1):
            if old != new:
                diffs.append((i, old.strip()[:150], new.strip()[:150]))

        changed_files += 1
        changed_lines += len(diffs)
        print(f"\n{rel}  ({len(diffs)} lines)")
        for ln, old, new in diffs:
            print(f"  {ln:>5} - {old}")
            print(f"        + {new}")

        if a.apply:
            p.write_text(out, encoding="utf-8")

    verb = "WROTE" if a.apply else "DRY RUN"
    print(f"\n{verb}: {changed_files} files, {changed_lines} lines")
    if not a.apply:
        print("re-run with --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
