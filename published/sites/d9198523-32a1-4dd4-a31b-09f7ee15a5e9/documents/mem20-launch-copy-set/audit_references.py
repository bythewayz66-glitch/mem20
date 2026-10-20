#!/usr/bin/env python3
"""
mem20 launch copy set — context-aware reference audit.

Naive grep produces false positives in two predictable ways (see skill pitfalls):
  1. Quoted prohibitions  -> the guardrail rule itself names the banned phrase.
  2. Change-log rows      -> the retired value legitimately appears in a
                             "Was (retired)" / "v2 (stale)" column.

So every hit is judged against a CONTEXT WINDOW, and a hit is compliant if the
window carries a negation/prohibition marker or the line sits in a retired
column of a labelled change table.
"""
import csv
import os
import re
import sys

# Resolve relative to THIS script so evidence is reproducible from any cwd.
ASSET_DIR = os.path.dirname(os.path.abspath(__file__))

# Files in scope: the v3 published assets only (prev_* are the read-only baseline).
ASSETS = [
    "mem20-launch-copy-pack.md",
    "readme-install-block.md",
    "show-hn-post.md",
    "product-hunt-post.md",
    "social-threads.md",
    "long-form-article.md",
    "landing-page-copy-update.md",
]

# --- patterns -------------------------------------------------------------
STALE_REPO = re.compile(r"JaysonAIOnline/(?:mem20|mcp-cognitive-substrate)", re.I)
STALE_ORG = re.compile(r"JaysonAIOnline", re.I)
# anchored: the bare command IS the published instruction
BARE_PIP = re.compile(r"^\s*pip install mem20\s*[;`]*\s*$")
STALE_PIN = re.compile(r"""pip install\s+["']?mcp\s*<\s*2""", re.I)
STALE_MODULE = re.compile(r"mcp_cognitive_substrate\.cli")
# retired tool-count ranges
STALE_COUNT = re.compile(r"~?258\s*[–-]\s*260|~258|~260|258 tools|260 tools")
BANNED = [
    re.compile(r"provably secure", re.I),
    re.compile(r"tamper[- ]proof", re.I),
    re.compile(r"unfakeable", re.I),
    re.compile(r"matches mem0", re.I),
    re.compile(r"beats zep", re.I),
    re.compile(r"industry[- ]leading", re.I),
]

CANONICAL = re.compile(r"github\.com/bythewayz66-glitch/mem20")
ADVERSARIAL = re.compile(r"0\.000\s+adversarial|adversarial[^.\n]{0,40}0\.000", re.I)
PIP_HOLD = re.compile(r"pip install mem20")
NOT_PYPI = re.compile(r"not (?:yet )?(?:published )?(?:to|on) PyPI|PyPI[^.\n]{0,30}404|404[^.\n]{0,30}PyPI", re.I)
COLLISION_WARN = re.compile(r"not (?:a valid|published)|do not use|isn't|is not\b", re.I)

NEGATION = re.compile(
    r"\b(never|not|no|absent|banned|avoid|do not|don't|instead|retired|superseded|"
    r"stale|obsolete|deprecated|was|formerly|previously|old[- ]org|dead)\b",
    re.I,
)

# A table row whose columns are explicitly labelled retired/stale is a change-log row.
RETIRED_ROW = re.compile(
    r"\|\s*(?:[^|]*\|\s*)?[^|]*(?:v2\s*\(stale\)|was \(retired\)|retired|stale|formerly)[^|]*\|",
    re.I,
)


def is_change_row(line):
    """True if the line is part of a table whose header labels a retired column."""
    if not line.strip().startswith("|"):
        return False
    return bool(RETIRED_ROW.search(line))


def in_retired_table(lines, idx):
    """Look upward for the nearest table header; if it labels a retired column, comply."""
    j = idx
    while j >= 0 and lines[j].strip().startswith("|"):
        j -= 1
    header = lines[j + 1] if j + 1 < len(lines) else ""
    return bool(re.search(r"stale|retired|was|v1|v2", header, re.I))


def window(lines, idx, radius=2):
    lo = max(0, idx - radius)
    hi = min(len(lines), idx + radius + 1)
    return "\n".join(lines[lo:hi])


def audit(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    lines = text.splitlines()

    res = {
        "file": path,
        "stale_repo_hits": 0,
        "stale_repo_assertive": 0,
        "bare_pip_install_mem20": 0,
        "stale_mcp_pin": 0,
        "stale_module_path": 0,
        "stale_tool_count": 0,
        "banned_phrase_assertive": 0,
        "canonical_repo_refs": 0,
        "adversarial_0_000_mentions": 0,
        "pypi_hold_mentions": 0,
        "no_locomo_disclaimer": 0,
        "evidence_based_promotion": 0,
        "self_reported_label": 0,
    }
    notes = []

    for i, line in enumerate(lines):
        win = window(lines, i)
        negated = bool(NEGATION.search(win))
        change = in_retired_table(lines, i)

        # stale repo path
        if STALE_ORG.search(line):
            res["stale_repo_hits"] += 1
            if not (negated or change):
                res["stale_repo_assertive"] += 1
                notes.append(f"L{i+1}: ASSERTIVE stale org ref -> {line.strip()[:110]}")

        # bare pip install mem20 (anchored only)
        if BARE_PIP.match(line):
            res["bare_pip_install_mem20"] += 1
            notes.append(f"L{i+1}: BARE pip install mem20 -> {line.strip()[:90]}")

        # stale pin / module / tool-count
        if STALE_PIN.search(line) and not negated and not change:
            res["stale_mcp_pin"] += 1
            notes.append(f"L{i+1}: ASSERTIVE stale mcp pin -> {line.strip()[:100]}")
        if STALE_MODULE.search(line) and not negated and not change:
            res["stale_module_path"] += 1
            notes.append(f"L{i+1}: ASSERTIVE stale module path -> {line.strip()[:100]}")
        if STALE_COUNT.search(line) and not negated and not change:
            res["stale_tool_count"] += 1
            notes.append(f"L{i+1}: ASSERTIVE stale tool count -> {line.strip()[:100]}")

        # banned phrases
        for pat in BANNED:
            if pat.search(line):
                if not (negated or change):
                    res["banned_phrase_assertive"] += 1
                    notes.append(f"L{i+1}: ASSERTIVE banned '{pat.pattern}' -> {line.strip()[:100]}")

        # positive counts
        res["canonical_repo_refs"] += len(CANONICAL.findall(line))
        res["adversarial_0_000_mentions"] += len(ADVERSARIAL.findall(line))
        res["pypi_hold_mentions"] += len(PIP_HOLD.findall(line))
        if re.search(r"LoCoMo", line, re.I):
            res["no_locomo_disclaimer"] += 1
        if re.search(r"evidence[- ]based promotion", line, re.I):
            res["evidence_based_promotion"] += 1
        if re.search(r"self[- ]reported", line, re.I):
            res["self_reported_label"] += 1

    # verdict
    failures = (
        res["stale_repo_assertive"]
        + res["bare_pip_install_mem20"]
        + res["stale_mcp_pin"]
        + res["stale_module_path"]
        + res["stale_tool_count"]
        + res["banned_phrase_assertive"]
    )
    res["verdict"] = "PASS" if failures == 0 else "FAIL"

    # disclosure requirement: any asset showing a benchmark table must disclose 0.000
    if re.search(r"hit rate", text, re.I) and res["adversarial_0_000_mentions"] == 0:
        res["verdict"] = "FAIL"
        notes.append("BENCHMARK TABLE WITHOUT 0.000 ADVERSARIAL DISCLOSURE")

    return res, notes


def main():
    rows, all_notes = [], []
    for name in ASSETS:
        path = os.path.join(ASSET_DIR, name)
        if not os.path.exists(path):
            print(f"MISSING: {path}", file=sys.stderr)
            return 2
        res, notes = audit(path)
        rows.append(res)
        all_notes.extend(f"{name} :: {n}" for n in notes)

    out = os.path.join(ASSET_DIR, "mem20-reference-audit.csv")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    width = max(len(r["file"]) for r in rows)
    print(f"{'file'.ljust(width)}  stale  pip  pin  mod  cnt  banned  canon  0.000  verdict")
    print("-" * (width + 52))
    for r in rows:
        print(
            f"{r['file'].ljust(width)}  "
            f"{r['stale_repo_assertive']:5d}  "
            f"{r['bare_pip_install_mem20']:3d}  "
            f"{r['stale_mcp_pin']:3d}  "
            f"{r['stale_module_path']:3d}  "
            f"{r['stale_tool_count']:3d}  "
            f"{r['banned_phrase_assertive']:6d}  "
            f"{r['canonical_repo_refs']:5d}  "
            f"{r['adversarial_0_000_mentions']:5d}  "
            f"{r['verdict']}"
        )

    print("\n--- notes ---")
    if all_notes:
        for n in all_notes:
            print(n)
    else:
        print("(none — no assertive violations)")

    total_fail = sum(1 for r in rows if r["verdict"] != "PASS")
    print(f"\n{len(rows) - total_fail}/{len(rows)} PASS | write -> {out}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
