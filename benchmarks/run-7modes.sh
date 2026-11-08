#!/usr/bin/env bash
# Canonical command that produced benchmarks/results/latest.{md,json}.
#
# Every scored row in latest.md names this script plus the dataset version and
# sha256 it ran against, so a row can be traced to a reproducible invocation
# without repeating a 200-character command 42 times in the table.
#
# Requirements: the mem20 repo checked out at the commit recorded in
# latest.json -> run_manifest.commit, and the reference cache under reference/v2/
# (the generator prints the exact curl commands if it is missing).
set -euo pipefail

CORPUS="${CORPUS:-/tmp/mem20-scale-corpus-v2}"
OUT="${OUT:-benchmarks/results}"

# Regenerate the corpus from the seeded generator. Deterministic: the resulting
# records.jsonl sha256 must equal run_manifest.corpus_sha256["records.jsonl"] in
# latest.json, or the generator changed and the published numbers are not
# comparable.
mem20benchmarkz generate-scale --out "$CORPUS"

# Score all seven modes. --bulk writes the ledger envelopes directly and
# rebuilds the vector/BM25/graph indexes once, instead of paying ~0.5 s per
# record through remember().
#
# KNOWN GAP (see docs/benchmarks/retrieval-gap-analysis-2026-11-01.md §5):
# the `_run_mode()` dispatch committed on main accepts only four of these seven
# ids -- semantic, hybrid, graph, keyword. It has no branch for `bm25`,
# `vector`, `hybrid-rerank-off` or `constant`, so re-running this script against
# main raises `ValueError: unsupported mode`. The seven-mode rows in
# latest.json are therefore not yet reproducible from main as committed; the
# corpus half is (all four sha256 match). Closing this needs the four missing
# branches, which is a harness change, not a reporting one.
mem20benchmarkz run-scale \
    --corpus "$CORPUS" \
    --bulk \
    --k 5 \
    --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant \
    --out "$OUT"
