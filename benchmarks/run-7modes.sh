#!/usr/bin/env bash
# Canonical command that produced benchmarks/results/latest.{md,json}.
#
# Every scored row in latest.md names this script plus the dataset version and
# sha256 it ran against, so a row can be traced to a reproducible invocation
# without repeating a 200-character command 42 times in the table.
#
# Requirements: the mem20 repo checked out at the commit recorded in
# latest.json -> provenance.commit, and the reference cache under reference/v2/
# (the generator prints the exact curl commands if it is missing).
set -euo pipefail

CORPUS="${CORPUS:-/tmp/mem20-scale-corpus-v2}"
OUT="${OUT:-benchmarks/results}"

# Regenerate the corpus from the seeded generator. Deterministic: the resulting
# dataset_sha256 must equal the one in latest.json, or the generator changed and
# the published numbers are not comparable.
mem20benchmarkz generate-scale --out "$CORPUS"

# Score all seven modes. --bulk writes the ledger envelopes directly and
# rebuilds the vector/BM25/graph indexes once, instead of paying ~0.5 s per
# record through remember().
mem20benchmarkz run-scale \
    --corpus "$CORPUS" \
    --bulk \
    --k 5 \
    --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant \
    --out "$OUT"
