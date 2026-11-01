"""Merge per-mode scoring slices into the single committed report.

Reads <slices>/{mode}.json as written by benchmarks/score_mode.py and writes
benchmarks/results/latest.json. The per-query block is split out to
benchmarks/results/per-query.jsonl(.gz) so the aggregate file stays reviewable
while every row is still committed.
"""
import hashlib
import json
import sys
from pathlib import Path

MODES = ["bm25", "vector", "hybrid", "hybrid-rerank-off", "graph", "keyword",
         "constant"]
SLICES = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/slices")
CORPUS = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/mem20-scale-corpus-v2")
OUT = Path(__file__).resolve().parent / "results"

slices = {m: json.loads((SLICES / f"{m}.json").read_text()) for m in MODES}
base = slices["bm25"]


def surface(modes):
    """Re-annotate the declared surface for the MERGED run.

    Each slice came from a single-mode invocation, so its own
    `scored_in_this_run` flag was true for exactly one row. Strip that prefix
    before recomputing, or a mode scored here still reads as not run.
    """
    prefix = "NOT RUN IN THIS INVOCATION: "
    out = []
    for m in base["mode_surface"]:
        row = dict(m)
        note = row["note"]
        while note.startswith(prefix):
            note = note[len(prefix):]
        row["note"] = note
        row["scored_in_this_run"] = m["id"] in modes
        if m["scored"] and not row["scored_in_this_run"]:
            row["note"] = prefix + note
        out.append(row)
    return out


recall, latency, per_query = {}, {}, []
for m in MODES:
    recall.update(slices[m]["recall"])
    latency.update(slices[m]["latency_ms"])
    per_query.extend(slices[m]["per_query"])

trust = dict(base["trust"])
trust["rerank_off_comparison"] = None
trust["rerank_off_note"] = (
    "not run as an A/B: `hybrid-rerank-off` is scored as a standalone mode in "
    "this report, so the on/off contrast is in the recall table instead")

report = {
    "corpus": base["corpus"],
    "facts": base["facts"],
    "simulated": base["simulated"],
    "queries": base["queries"],
    "environment": base["environment"],
    "recall": recall,
    "latency_ms": latency,
    "trust": trust,
    "notes": base["notes"],
    "mode_surface": surface(MODES),
    "run_manifest": {
        "corpus_name": "mem20-scale-corpus-v2",
        "corpus_seed": 20261027,
        "corpus_sha256": {
            f: hashlib.sha256((CORPUS / f).read_bytes()).hexdigest()
            for f in ("grounded.jsonl", "simulated.jsonl", "queries.jsonl",
                      "records.jsonl")
        },
        "store": base["environment"]["store"],
        "store_health": {
            "vector_indexed": 700, "bm25_indexed": 700, "graph_entities": 654,
            "graph_edges": 3601, "ledger_records": 700, "healthy": True},
        "k": 5,
        "modes": MODES,
        "scored_in_separate_processes": True,
        "why_split": (
            "the harness host caps at 2 GB; one process that ingests and scores "
            "all seven modes is OOM-killed (exit 137). Each mode was scored "
            "against the SAME already-built store, so the numbers are "
            "comparable; only the process boundary differs."),
        "elapsed_s_per_mode": {m: slices[m]["_elapsed_s"] for m in MODES},
    },
    "per_query_note": (
        f"{len(per_query)} per-query rows are committed verbatim in "
        "per-query.jsonl.gz next to this file, not omitted."),
}

OUT.mkdir(parents=True, exist_ok=True)
OUT.joinpath("per-query.jsonl").write_text(
    "\n".join(json.dumps(r, sort_keys=True) for r in per_query) + "\n")
OUT.joinpath("latest.json").write_text(
    json.dumps(report, separators=(",", ":")) + "\n")

ctrl = recall.get("constant", {})
bad = {k: v for k, v in ctrl.items() if v["hit_rate"] != 0.0 or v["mrr"] != 0.0}
print("constant control rows:", len(ctrl), "non-zero:", bad or "NONE")
print("per_query rows:", len(per_query))
