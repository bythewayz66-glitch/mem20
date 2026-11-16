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

# Score every mode the store exposes. --bulk writes the ledger envelopes
# directly and rebuilds the vector/BM25/graph indexes once, instead of paying
# ~0.5 s per record through remember().
#
# The mode list is the full surface, not a subset. `_run_mode()` now has a
# branch for all eleven ids, so this script is reproducible from the branch it
# ships on. The four modes that were previously declared but unscored
# (`recall`, `recall_at`, `entities`, `ledger`) are answered by a different
# store surface than a text ranker, so each is scored only on the probe class
# it can legitimately answer — see `_mode_answers_kind()` in bench.py.
#
# `graph` is scored on `multi_hop` AND `graph_hop`, so its n is 90 rather than
# the 30 multi_hop probes alone.
mem20benchmarkz run-scale \
    --corpus "$CORPUS" \
    --bulk \
    -k 5 \
    --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant,recall,recall_at,entities,ledger \
    --out "$OUT"
