# mem20 retrieval benchmarks — four-mode run (2026-10-31)

Corpus `mem20-scale-corpus-v2` — 700 grounded facts, 1,300 simulated facts, 250 queries.
Generated offline from the cached reference set (`reference/v2/`, seed `20261027`) and
validated before scoring: **PASS (0 errors, 230 answerable probes checked)**.

> [!IMPORTANT]
> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo (92.5) and
> LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the
> three are private or vendor-defined — and different metrics. Nothing here refutes or
> reproduces them. These results describe this corpus only.

## Why this run exists

`benchmarks/results/latest.md` published only `keyword` and `semantic`. The harness has
always supported `hybrid` and `graph` (`bench.py` dispatches all four), so the published
table understated the surface it claimed to measure. This run scores all four.

## Retrieval quality

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `keyword` | adversarial | 60 | 0.167 | 0.167 | 0.000 | 306.2 |
| `keyword` | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 301.6 |
| `keyword` | contradiction | 40 | 0.125 | 0.108 | 0.000 | 302.3 |
| `keyword` | direct | 60 | 1.000 | 0.983 | 0.000 | 297.8 |
| `keyword` | multi_hop | 30 | 0.467 | 0.467 | 0.000 | 300.2 |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 309.7 |
| `semantic` | adversarial | 60 | 0.667 | 0.608 | 0.000 | 89.1 |
| `semantic` | adversarial_hard | 40 | 0.750 | 0.583 | 0.000 | 86.3 |
| `semantic` | contradiction | 40 | 1.000 | 1.000 | 0.000 | 87.7 |
| `semantic` | direct | 60 | 0.900 | 0.864 | 0.000 | 83.6 |
| `semantic` | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 88.5 |
| `semantic` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 91.4 |
| `hybrid` | adversarial | 60 | 0.167 | 0.167 | 0.000 | 306.2 |
| `hybrid` | adversarial_hard | 40 | 0.050 | 0.050 | 0.000 | 301.9 |
| `hybrid` | contradiction | 40 | 1.000 | 0.988 | 0.000 | 299.9 |
| `hybrid` | direct | 60 | 1.000 | 0.978 | 0.000 | 297.5 |
| `hybrid` | multi_hop | 30 | 0.533 | 0.533 | 0.000 | 296.8 |
| `hybrid` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 314.3 |
| `graph` | multi_hop | 30 | 0.033 | 0.033 | 0.000 | 13.5 |

`graph` is scored only on `multi_hop` by design — `bench.py` skips it for every other query
kind because graph traversal is only meaningful for entity queries.

## Latency

| Mode | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| `graph` | 30 | 13.4 | 238.3 | 244.0 | 244.0 |
| `hybrid` | 250 | 301.7 | 400.5 | 504.1 | 690.2 |
| `keyword` | 250 | 302.5 | 399.8 | 511.6 | 600.6 |
| `semantic` | 250 | 87.5 | 98.6 | 102.5 | 309.5 |

## Trustworthiness

| Check | Value | Required |
|---|---:|---|
| Contamination rate | 0.0 | 0.0 |
| Simulated records in BM25 corpus | [] | 0 |
| Stale pointer rate | 0.000000 | 0.0 |
| Index healthy | True | True |
| Ledger records | 700 | — |
| Graph entities / edges | 654 / 3601 | — |
| Queries reporting a diagnostic | 780 | — |
| All reported healthy | True | True |

## What this run changes in the published claim

1. **`hybrid` is not the best mode on this corpus.** It ties `keyword` on adversarial
   (0.167) and loses to `semantic` on adversarial (0.667), adversarial_hard (0.750 vs
   0.050) and multi_hop (1.000 vs 0.533). The README's "Default. Best recall" line for
   `recall_hybrid()` is not supported by these numbers.
2. **`graph` scores 0.033 on multi_hop**, against 1.000 for `semantic`. The README's
   "graph (multi-hop) 1.000" row is from the 13-query `mem20-agent-kb-v1` corpus, not this
   one, and does not reproduce at 250 queries.
3. **`keyword` adversarial is 0.167, not 0.000.** The 0.000 adversarial row that the
   README and launch copy carry is a `mem20-agent-kb-v1` figure. On the scale corpus the
   honest number is 0.167 for keyword/hybrid and 0.667 for semantic.
4. **Latency regressed against the published table** (keyword p50 112.0 → 302.5 ms). This
   run had no warm cache and ran under a shared 4 GB sandbox, so treat the latency column
   as indicative, not as a like-for-like comparison.

The adversarial weakness is real and is not being retired: `adversarial_hard` at 0.025
(keyword) and 0.050 (hybrid) is the honest floor, and `unanswerable` is 0.000 everywhere,
which is the correct control result.

## Environment

- Python 3.11.15 on Linux-6.8.0-90-generic-x86_64-with-glibc2.36 (x86_64)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Vector deps available: True; BM25: True; cross-encoder: True
- Isolated store per run; live data never touched

## Reproduce

```bash
mkdir -p reference/v2   # cached reference data, fetched once
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes keyword,semantic,hybrid,graph --out benchmarks/results
```

### Known harness defect found by this run

`run-scale` scores correctly and prints the full report, then crashes in
`cmd_run_scale` at `print(f"wrote {paths['json']}")` with
`TypeError: 'NoneType' object is not subscriptable` — `save()` returned `None` because the
`--out` directory did not exist. The scores above were captured from stdout; the JSON and
markdown were not written. Fix: `mkdir -p` the out dir before `save()`, or have `save()`
create it. Tracked as a defect, not worked around silently.
