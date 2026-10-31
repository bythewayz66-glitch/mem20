# mem20 retrieval benchmarks

Corpus `mem20-scale-corpus-v2` — 700 grounded facts, 1300 simulated facts, 250 queries.

> [!IMPORTANT]
> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here refutes or reproduces them. These results describe this corpus only.

## Retrieval quality

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `keyword` | adversarial | 60 | 1.000 | 1.000 | 0.000 | 110.2 |
| `keyword` | adversarial_hard | 40 | 0.000 | 0.000 | 0.000 | 192.1 |
| `keyword` | contradiction | 40 | 0.050 | 0.030 | 0.000 | 184.5 |
| `keyword` | direct | 60 | 1.000 | 1.000 | 0.000 | 146.8 |
| `keyword` | multi_hop | 30 | 0.800 | 0.800 | 0.000 | 184.9 |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 108.8 |
| `semantic` | adversarial | 60 | 0.950 | 0.884 | 0.000 | 102.3 |
| `semantic` | adversarial_hard | 40 | 0.900 | 0.810 | 0.000 | 102.1 |
| `semantic` | contradiction | 40 | 1.000 | 1.000 | 0.000 | 104.3 |
| `semantic` | direct | 60 | 0.900 | 0.864 | 0.000 | 103.0 |
| `semantic` | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 105.3 |
| `semantic` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 105.8 |

## Latency

| Mode | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| `keyword` | 250 | 112.0 | 203.4 | 289.8 | 419.7 |
| `semantic` | 250 | 103.5 | 195.4 | 291.6 | 438.8 |

## Trustworthiness

This is the axis mem20 claims as its differentiator, and the one no competitor publishes. A system that answers confidently from a stale index can look good on hit rate and fail here.

| Check | Value | Required |
|---|---:|---|
| Contamination rate | 0.0 | 0.0 |
| Simulated records in BM25 corpus | [] | 0 |
| Stale pointer rate | 0.000000 | 0.0 |
| Index healthy | True | True |
| Ledger records | 700 | — |
| Graph entities / edges | 654 / 3601 | — |
| Queries reporting a diagnostic | 500 | — |
| All reported healthy | True | True |

## Environment

- Python 3.11.15 on Linux-6.8.0-142-generic-x86_64-with-glibc2.36 (x86_64)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Vector deps available: True; BM25: True; cross-encoder: True

## Notes

- Scores are NOT comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR. Those run on different corpora (two of them private or vendor-defined) with different metrics. These numbers describe this corpus only.
- 500 per-query rows are omitted from the committed results files. This is a **trimmed** artifact: `docs/benchmarks/render.py --check` exits 3 on it (`artifact has no per_query rows; cannot verify aggregates`), so the aggregates above cannot be re-derived from the committed file alone. Re-run the harness to regenerate them.
- The seed is `SCALE_SEED = 20261027` in `mem20benchmarkz/mem20benchmarkz/scale_corpus.py`. The harness has **no `--seed` flag**; the seed is a corpus constant, not a run argument.

## Reproducibility status

What was re-verified for this revision, and what was not:

| Step | Status |
|---|---|
| `generate-scale` produces 2,000 records / 250 probes | **re-verified** |
| `validate-scale` → PASS, 0 errors, 230 answerable probes | **re-verified** |
| `records.jsonl` byte-determinism across two runs | **re-verified** (identical sha256) |
| The retrieval run behind the table above | **not re-executed** — see below |

The retrieval numbers in the table are the committed measurement from the environment recorded in `latest.json`. They were **not** re-executed for this revision: the audit environment has no embedding stack (`sentence-transformers`, `faiss-cpu`, `rank-bm25` absent), so the store reports `healthy: false` and `run-scale` correctly refuses to score (exit 2). Treat the table as a recorded measurement, not as a number re-verified today.

## Reproduce

```bash
# 1. Fetch the offline reference cache. It is NOT committed: generate-scale
#    fails with FileNotFoundError on a clean clone until these three files exist.
mkdir -p reference/v2
curl -sL -o reference/v2/periodic-table.json https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json
curl -sL -o reference/v2/iso-3166.json https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json
curl -sL -o reference/v2/mime-db.json https://raw.githubusercontent.com/jshttp/mime-db/master/db.json

# 2. Generate + validate the corpus (deterministic; seed is a source constant).
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2

# 3. Score. Requires sentence-transformers + faiss-cpu + rank-bm25; without them
#    the store is unhealthy and run-scale refuses to score (exit 2).
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes keyword,semantic --out benchmarks/results
```

The run uses an isolated store, ingests the corpus through the engine's own ledger and index build paths, and never touches live data.
