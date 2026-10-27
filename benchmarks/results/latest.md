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
- 500 per-query rows are omitted from the committed results files; re-run the harness at seed 20261027 to reproduce them.

## Reproduce

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes keyword,semantic --out benchmarks/results
```

The run uses an isolated store, ingests the corpus through the engine's own ledger and index build paths, and never touches live data.
