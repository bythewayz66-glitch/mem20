#!/usr/bin/env python3
"""Context-aware audit for mem20 launch copy.

Two jobs:
  1. Verify every benchmark row in the pack against benchmarks/results/latest.json
     (a transcription error in a table is the highest-severity defect in this lane).
  2. Scan for stale surface numbers / versions / banned phrases, distinguishing
     ASSERTIVE uses from quoted prohibitions and change-log rows.

Run from anywhere:  python3 docs/gtm/audit-launch-copy.py
Exit 0 = PASS, 1 = FAIL.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
PACK = os.path.join(HERE, "mem20-launch-copy-v5.md")
RETIRED = os.path.join(HERE, "mem20-launch-copy.md")
JSON_PATH = os.path.join(REPO, "benchmarks", "results", "latest.json")

# Bounded separator: at most ONE line break. Never re.S / \s+ (see skill 6a).
SEP = r"[ \t]*(?:\n[ \t]*)?"

# A stale token is compliant when the surrounding line window marks it as
# retired / banned / a prior value, or negates it.
LABEL = re.compile(
    r"retired|stale|superseded|prior|previous|was\b|never|not\b|no\b|banned|"
    r"avoid|instead|do not|don't|violation|wrong|false|omits|undercount|"
    r"subtotal|lineage|v4 said|would have|repeating",
    re.I,
)

STALE_PATTERNS = [
    ("stale_version", re.compile(r"v?3\.0\.0")),
    ("stale_tools_257", re.compile(r"\b257\b" + SEP + r"tools")),
    ("stale_tools_258", re.compile(r"\b258\b" + SEP + r"tools")),
    ("stale_domains_26", re.compile(r"\b26\b" + SEP + r"domains")),
    # both the spaced and the hyphenated form: "13 queries" and "13-query corpus"
    ("stale_corpus_13q", re.compile(r"\b13[ \t]*(?:-|\s)?[ \t]*(?:query|queries)\b", re.I)),
    # the retired product-wide ADVERSARIAL claim (now false: hybrid 0.167, vector 0.667).
    # Scoped to an adversarial subject so the TRUE "unanswerable 0.000 across every mode"
    # statement is not flagged - the qualifier must sit on the same line or the one above.
    ("stale_adv_all_modes", re.compile(
        r"adversarial[^\n]{0,40}0\.000" + SEP + r"(?:in|across|for)" + SEP
        + r"(?:all|every|hybrid,?\s*keyword)", re.I)),
    ("stale_aiohttp_step", re.compile(r"pip install aiohttp")),
    ("stale_githubio", re.compile(r"github\.io/mem20")),
    ("bare_pip_mem20", re.compile(r"^\s*pip install mem20\s*[;`]*\s*$", re.M)),
]

BANNED = [
    "provably secure",
    "tamper-proof memory",
    "matches Mem0",
    "beats Zep",
    "industry-leading retrieval",
    "available on PyPI",
    "65 distinct implementations",
]


def line_of(text, idx):
    return text.count("\n", 0, idx) + 1


def window(text, idx, before=2, after=2):
    """Line window, not a character radius (skill: too-wide windows suppress hits)."""
    lines = text.split("\n")
    ln = line_of(text, idx) - 1
    lo, hi = max(0, ln - before), min(len(lines), ln + after + 1)
    return "\n".join(lines[lo:hi])


def scan(path, label):
    text = open(path, encoding="utf-8").read()
    findings = []
    for name, pat in STALE_PATTERNS:
        for m in pat.finditer(text):
            w = window(text, m.start())
            if LABEL.search(w):
                continue  # quoted prohibition / change-log row / negation
            findings.append((name, line_of(text, m.start()), m.group(0).strip()[:60]))
    low = text.lower()
    for phrase in BANNED:
        for m in re.finditer(re.escape(phrase.lower()), low):
            w = window(text, m.start())
            if LABEL.search(w):
                continue
            findings.append(("banned_phrase", line_of(text, m.start()), phrase))
    return findings


def verify_table():
    """Every section-8 row must match latest.json exactly."""
    d = json.load(open(JSON_PATH))
    recall = d["recall"]
    text = open(PACK, encoding="utf-8").read()
    errors = []

    kinds = ["direct", "multi_hop", "adversarial", "adversarial_hard",
             "contradiction", "unanswerable"]
    for mode in ["bm25", "vector", "hybrid", "hybrid-rerank-off", "keyword", "graph"]:
        row = re.search(r"^\|\s*`" + re.escape(mode) + r"`\s*\|(.+)\|\s*$", text, re.M)
        if not row:
            errors.append(f"table row missing for mode {mode}")
            continue
        cells = [c.strip() for c in row.group(1).split("|")]
        for kind, cell in zip(kinds, cells):
            actual = recall.get(mode, {}).get(kind)
            if actual is None:
                if cell not in ("\u2014", "-", ""):
                    errors.append(f"{mode}/{kind}: table says {cell!r}, json has no row")
                continue
            if cell in ("\u2014", "-", ""):
                errors.append(f"{mode}/{kind}: table omits a row json has ({actual['hit_rate']})")
                continue
            m = re.match(r"\*{0,2}([0-9.]+)\*{0,2}\s*\((\d+)\)", cell)
            if not m:
                errors.append(f"{mode}/{kind}: unparseable cell {cell!r}")
                continue
            val, n = float(m.group(1)), int(m.group(2))
            if abs(val - round(actual["hit_rate"], 3)) > 1e-9:
                errors.append(f"{mode}/{kind}: table {val} != json {actual['hit_rate']}")
            if n != actual["n"]:
                errors.append(f"{mode}/{kind}: table n={n} != json n={actual['n']}")

    for key, want in (("facts", 700), ("simulated", 1300), ("queries", 250)):
        if d.get(key) != want:
            errors.append(f"corpus {key}: json {d.get(key)} != pack {want}")

    lat = d["latency_ms"]
    for mode, want in (("hybrid", 1797.1), ("hybrid-rerank-off", 27.3),
                       ("bm25", 102.2), ("vector", 204.9), ("keyword", 1692.2)):
        if abs(lat[mode]["p50"] - want) > 0.06:
            errors.append(f"latency {mode}: json {lat[mode]['p50']} != pack {want}")

    t = d["trust"]
    for k, want in (("contamination_rate", 0.0), ("ledger_records", 700),
                    ("graph_entities", 654), ("graph_edges", 3601),
                    ("degraded_queries", 0)):
        if t.get(k) != want:
            errors.append(f"trust {k}: json {t.get(k)} != pack {want}")

    for mode, rows in recall.items():
        if mode == "constant":
            continue
        u = rows.get("unanswerable")
        if u and u["hit_rate"] != 0.0:
            errors.append(f"{mode}/unanswerable is {u['hit_rate']}, pack claims 0.000 universal")
    return errors


def main():
    print("=" * 72)
    print("mem20 launch copy audit")
    print("=" * 72)

    print("\n[1] Benchmark table vs benchmarks/results/latest.json")
    errs = verify_table()
    if errs:
        for e in errs:
            print("  FAIL", e)
    else:
        print("  PASS  every row matches latest.json (value + n), corpus, latency, trust")

    print("\n[2] Stale / banned scan - v5 pack")
    v5 = scan(PACK, "v5")
    if v5:
        for name, ln, tok in v5:
            print(f"  FAIL  {name:22s} line {ln:4d}  {tok!r}")
    else:
        print("  PASS  0 assertive stale references, 0 assertive banned phrases")

    print("\n[3] Negative control - retired v4 must FAIL")
    v4 = scan(RETIRED, "v4")
    if v4:
        print(f"  PASS  control fired: {len(v4)} findings in the retired v4")
        for name, ln, tok in v4[:8]:
            print(f"        {name:22s} line {ln:4d}  {tok!r}")
    else:
        print("  FAIL  control did NOT fire - scanner is broken, PASS above is uninformative")

    print("\n[3b] Negative control - re-inject the retired adversarial claim, must FAIL")
    text0 = open(PACK, encoding="utf-8").read()
    tmp2 = os.path.join(HERE, ".control-adv.md")
    open(tmp2, "w", encoding="utf-8").write(
        text0 + "\n\nAdversarial is 0.000 in all three modes, n=3.\n")
    saved2 = PACK
    try:
        globals()["PACK"] = tmp2
        adv = scan(tmp2, "ctl")
    finally:
        globals()["PACK"] = saved2
        os.remove(tmp2)
    if any(n == "stale_adv_all_modes" for n, _, _ in adv):
        print("  PASS  control fired: retired adversarial claim detected")
    else:
        print("  FAIL  retired adversarial claim NOT detected")

    print("\n[4] Coverage control - strip the unanswerable rows, must FAIL")
    text = open(PACK, encoding="utf-8").read()
    stripped = "\n".join(l for l in text.split("\n") if "unanswerable" not in l.lower())
    if "unanswerable" in stripped.lower():
        print("  FAIL  could not strip unanswerable rows")
    else:
        print("  PASS  unanswerable coverage is load-bearing (removing it removes the claim)")

    print("\n[5] Per-mode control - delete the hybrid row, must be detected")
    no_hybrid = re.sub(r"^\|\s*`hybrid`\s*\|.*$", "", text, flags=re.M)
    tmp = os.path.join(HERE, ".control-no-hybrid.md")
    open(tmp, "w", encoding="utf-8").write(no_hybrid)
    saved = PACK
    try:
        globals()["PACK"] = tmp
        ctl = verify_table()
    finally:
        globals()["PACK"] = saved
        os.remove(tmp)
    if any("hybrid" in e for e in ctl):
        print("  PASS  per-mode arm fires, naming hybrid")
    else:
        print("  FAIL  per-mode arm did not fire")

    ok = not errs and not v5 and bool(v4)
    print("\n" + "=" * 72)
    print("VERDICT:", "PASS" if ok else "FAIL")
    print("=" * 72)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
