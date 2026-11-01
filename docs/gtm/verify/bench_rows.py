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
    print()
    print("=== latest.md vs latest.json ===")
    print("json trust.queries_with_drift_diagnostic = %s"
          % d["trust"]["queries_with_drift_diagnostic"])
    print("json per_query_note = %s" % d.get("per_query_note"))
    print()
    print("json latency p50 per mode:")
    for m, v in d["latency_ms"].items():
        print("  %-20s p50=%s" % (m, v["p50"]))
    print()
    print("json recall median_latency_ms per mode/kind (first kind only):")
    for m, rows in d["recall"].items():
        first = next(iter(rows.values()))
        print("  %-20s %s" % (m, first["median_latency_ms"]))
    print()
    print("--- claims made by latest.md that the json does not support ---")
    print("1. per-row 'p50 ms' column: md prints 5.2 / 18.5 / 168.5 / 173.5 for")
    print("   bm25 / vector / hybrid / keyword; json latency_ms p50 is")
    print("   102.2 / 204.94 / 1797.13 / 1692.2. The md column is not the json p50.")
    print("2. md 'Queries reporting a diagnostic 1530' vs json")
    print("   trust.queries_with_drift_diagnostic = %s."
          % d["trust"]["queries_with_drift_diagnostic"])
    print("   1530 is the per-query ROW count (250 probes x 6 text modes + 30 graph),")
    print("   not a count of queries reporting a diagnostic.")
    print("3. json per_query_note claims per-query.jsonl.gz is committed next to the")
    print("   file. It is absent: `ls benchmarks/results/` shows only latest.md/json.")
    print("4. benchmarks/run-7modes.sh says it reads latest.json -> provenance.commit")
    print("   and dataset_sha256. Neither key exists in latest.json.")
    print("5. latest.md cites dataset sha256 c7031ab7ac08; latest.json carries only")
    print("   per-file sha256s under run_manifest.corpus_sha256, no dataset_sha256.")


def main():
    d = load()
    matrix(d)
    weakest(d)
    trust(d)
    if "--discrepancies" in sys.argv:
        discrepancies(d)


if __name__ == "__main__":
    main()
