#!/usr/bin/env python3
"""Settling command for the benchmark rows in docs/gtm/claim-ledger.md.

Prints the shipped retrieval matrix from benchmarks/results/latest.json, the
weakest rows, the trust block, and (with --discrepancies) every place where
latest.md and latest.json disagree.

Usage:
    python3 docs/gtm/verify/bench_rows.py
    python3 docs/gtm/verify/bench_rows.py --discrepancies
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
JSON_PATH = os.path.join(ROOT, "benchmarks", "results", "latest.json")
MD_PATH = os.path.join(ROOT, "benchmarks", "results", "latest.md")

KINDS = ["adversarial", "adversarial_hard", "contradiction",
         "direct", "multi_hop", "unanswerable"]


def load():
    with open(JSON_PATH) as f:
        return json.load(f)


def matrix(d):
    r = d["recall"]
    print("corpus=%s facts=%s simulated=%s queries=%s"
          % (d["corpus"], d["facts"], d["simulated"], d["queries"]))
    print("modes scored: %s" % ", ".join(r.keys()))
    print()
    hdr = "%-20s" % "mode" + "".join("%18s" % k for k in KINDS)
    print(hdr)
    print("-" * len(hdr))
    for mode, rows in r.items():
        line = "%-20s" % mode
        for k in KINDS:
            v = rows.get(k)
            line += "%18s" % ("%.4f/n=%d" % (v["hit_rate"], v["n"]) if v else "-")
        print(line)


def weakest(d):
    print()
    print("=== weakest scored rows (hit_rate ascending) ===")
    flat = []
    for mode, rows in d["recall"].items():
        if mode == "constant":
            continue
        for k, v in rows.items():
            flat.append((v["hit_rate"], mode, k, v["n"], v["mrr"], v["leak_rate"]))
    for hit, mode, k, n, mrr, leak in sorted(flat)[:8]:
        print("  %-20s %-18s hit=%.4f n=%-3d mrr=%.4f leak=%.3f"
              % (mode, k, hit, n, mrr, leak))


def trust(d):
    print()
    print("=== trust block ===")
    for k, v in d["trust"].items():
        print("  %-32s %s" % (k, v))


def discrepancies(d):
    """Check latest.md against latest.json instead of asserting old drift.

    This block used to hardcode five disagreements (a p50 column that was not
    the json p50, a trust row reporting the per-query row count, a phantom
    per-query.jsonl.gz, and two provenance keys that never existed). Those were
    real, and they are fixed: latest.md is now rendered from latest.json by
    benchmarks/render_latest_md.py. Asserting them here would make the verifier
    lie in the other direction, so it now measures.
    """
    import re
    print()
    print("=== latest.md vs latest.json ===")
    with open(MD_PATH) as f:
        md = f.read()

    problems = []

    # 1. every per-kind p50 cell must equal recall.<mode>.<kind>.median_latency_ms
    rows = re.findall(
        r"^\| `([a-z0-9-]+)` \| ([a-z_]+) \| (\d+) \| ([\d.]+) \| ([\d.]+) \| "
        r"([\d.]+) \| ([\d.]+) \|", md, re.M)
    for mode, kind, n, hit, mrr, leak, p50 in rows:
        cell = d["recall"].get(mode, {}).get(kind)
        if cell is None:
            problems.append(f"md row {mode}/{kind} has no json cell")
            continue
        if int(n) != cell["n"]:
            problems.append(f"{mode}/{kind}: n {n} != {cell['n']}")
        for label, got, want in (("hit", hit, cell["hit_rate"]),
                                 ("mrr", mrr, cell["mrr"]),
                                 ("leak", leak, cell["leak_rate"]),
                                 ("p50", p50, cell["median_latency_ms"])):
            if abs(float(got) - want) > 0.06:
                problems.append(f"{mode}/{kind}: {label} {got} != {want}")

    # 2. the trust row must be the json value, not the per-query row count
    want = d["trust"]["queries_with_drift_diagnostic"]
    if f"| Queries reporting a drift diagnostic | {want} |" not in md:
        problems.append(
            f"md trust row is not json queries_with_drift_diagnostic={want}")

    # 3. no phantom per-query.jsonl.gz claim anywhere in the artifact
    if "per-query.jsonl.gz" in md or "per-query.jsonl.gz" in json.dumps(d):
        problems.append("phantom per-query.jsonl.gz claim still present")

    # 4. the dataset digest cited in md must be a real run_manifest digest
    digests = set(d["run_manifest"]["corpus_sha256"].values())
    for cited in re.findall(r"sha256 `([0-9a-f]{12})", md):
        if not any(x.startswith(cited) for x in digests):
            problems.append(f"md cites sha256 {cited} not in run_manifest")

    if problems:
        print("DRIFT (%d):" % len(problems))
        for p in problems:
            print("  -", p)
    else:
        print("OK: latest.md matches latest.json on every checked cell")
    print()
    print("json per_query_note = %s" % d.get("per_query_note"))


def main():
    d = load()
    matrix(d)
    weakest(d)
    trust(d)
    if "--discrepancies" in sys.argv:
        discrepancies(d)


if __name__ == "__main__":
    main()
