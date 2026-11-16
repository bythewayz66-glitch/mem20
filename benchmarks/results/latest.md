# mem20 retrieval benchmarks

Corpus `mem20-scale-corpus-v2` — 700 grounded facts, 1300 simulated facts, 410 queries.

> [!IMPORTANT]
> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo and LongMemEval figures and Zep's DMR come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here refutes or reproduces them. These results describe this corpus only. No competitor figure is quoted in this report, by design: a number lifted out of context is exactly how an incomparable result gets mistaken for a comparable one.

> [!WARNING]
> **No LoCoMo result is claimed.** This harness has not been run against the LoCoMo originals (10 conversations, 1,986 QA). No LoCoMo figure appears in this report and none may be quoted from it. The caveat stays until a run on the originals lands.

## Retrieval quality

Every row below names the dataset version and the exact command that produced it, so a number can be traced back to a reproducible run rather than to a report. This file is rendered from `latest.json` by `benchmarks/render_latest_md.py`; the JSON is the artifact of record.

- Dataset: `mem20-scale-corpus-v2` (`records.jsonl` sha256 `28f0746be240…`, 2000 records, 410 probes)
- Run command: `mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk -k 5 --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant,recall,recall_at,entities,ledger --out benchmarks/results`
- Canonical script: `benchmarks/run-7modes.sh` (the command above, parameterised; every row below names it)
- Commit: `0224a64946a2c00313a9872515893157adcbc47e`; k=5; embedding threads=1

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms | Dataset | Run command |
|---|---|---:|---:|---:|---:|---:|---|---|
| `bm25` | direct | 60 | 1.000 | 1.000 | 0.000 | 5.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `bm25` | adversarial | 60 | 0.767 | 0.378 | 0.000 | 5.2 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `bm25` | adversarial_hard | 40 | 1.000 | 0.846 | 0.000 | 5.1 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `bm25` | contradiction | 40 | 1.000 | 0.912 | 0.000 | 5.2 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `bm25` | multi_hop | 30 | 1.000 | 0.694 | 0.000 | 5.2 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `bm25` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 5.2 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `bm25` | graph_hop | 60 | 1.000 | 1.000 | 0.000 | 5.1 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | direct | 60 | 0.767 | 0.526 | 0.000 | 6.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | adversarial | 60 | 0.067 | 0.025 | 0.000 | 6.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | adversarial_hard | 40 | 0.225 | 0.142 | 0.000 | 6.9 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | contradiction | 40 | 0.975 | 0.801 | 0.000 | 6.9 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | multi_hop | 30 | 0.700 | 0.650 | 0.000 | 6.9 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 6.9 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `vector` | graph_hop | 60 | 0.933 | 0.739 | 0.000 | 6.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | direct | 60 | 0.867 | 0.825 | 0.000 | 12.3 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | adversarial | 60 | 0.150 | 0.126 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | adversarial_hard | 40 | 0.375 | 0.271 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | contradiction | 40 | 1.000 | 0.963 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | multi_hop | 30 | 0.800 | 0.719 | 0.000 | 12.6 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 12.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid` | graph_hop | 60 | 0.933 | 0.832 | 0.000 | 12.3 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | direct | 60 | 0.867 | 0.825 | 0.000 | 12.2 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | adversarial | 60 | 0.150 | 0.126 | 0.000 | 12.7 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | adversarial_hard | 40 | 0.375 | 0.271 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | contradiction | 40 | 1.000 | 0.963 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | multi_hop | 30 | 0.800 | 0.719 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 12.7 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | graph_hop | 60 | 0.933 | 0.832 | 0.000 | 12.3 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `graph` | multi_hop | 30 | 0.033 | 0.033 | 0.000 | 15.3 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `graph` | graph_hop | 60 | 0.750 | 0.613 | 0.000 | 15.9 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | direct | 60 | 1.000 | 1.000 | 0.000 | 12.4 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | adversarial | 60 | 0.767 | 0.378 | 0.000 | 12.7 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | adversarial_hard | 40 | 1.000 | 0.846 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | contradiction | 40 | 1.000 | 0.887 | 0.000 | 12.6 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | multi_hop | 30 | 1.000 | 0.694 | 0.000 | 12.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 12.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `keyword` | graph_hop | 60 | 1.000 | 1.000 | 0.000 | 12.6 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | direct | 60 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | adversarial | 60 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | adversarial_hard | 40 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | contradiction | 40 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | multi_hop | 30 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `constant` | graph_hop | 60 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `recall` | recall | 30 | 1.000 | 1.000 | 0.000 | 2.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `recall_at` | recall_at | 30 | 1.000 | 1.000 | 0.000 | 2.9 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `entities` | entities | 20 | 1.000 | 0.542 | 0.000 | 198.8 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |
| `ledger` | ledger | 20 | 1.000 | 0.457 | 0.000 | 2.5 | `mem20-scale-corpus-v2@28f0746be240` | `benchmarks/run-7modes.sh` |

### Adversarial control

`constant` ignores the query and always returns one fixed document that matches no corpus record. Every metric below must read exactly **0.000**; a non-zero value means the metric is handing out free hits.

| Query kind | n | Hit rate | MRR |
|---|---:|---:|---:|
| direct | 60 | 0.000 | 0.000 |
| adversarial | 60 | 0.000 | 0.000 |
| adversarial_hard | 40 | 0.000 | 0.000 |
| contradiction | 40 | 0.000 | 0.000 |
| multi_hop | 30 | 0.000 | 0.000 |
| unanswerable | 20 | 0.000 | 0.000 |
| graph_hop | 60 | 0.000 | 0.000 |

## Mode surface

Every retrieval mode present in the tree, whether this run scored it, and — where it did not — the reason. A mode is never dropped from this table: an absent row reads as "not run", which is a different and weaker statement than "blocked and documented".

| Mode | Surface | Scored | In this run | Note |
|---|:--:|:--:|:--:|---|
| `bm25` | engine BM25 index (rank_bm25), vector half never called | yes | yes | Pure sparse retrieval. Reads the engine's own bm25_index.pkl / bm25_corpus.jsonl, so it measures the index the store built. NOT the same as `keyword`: hybrid(alpha=0.0) still executes the vector half and fuses it, so calling that BM25 overstates what was isolated. |
| `vector` | MemoryStore.semantic -> recall_semantic (FAISS) | yes | yes | Dense retrieval. ALIAS of `semantic`, not a second system: same code path, scored under the name the surface list uses. The embedder backend is reported in `environment.embedder_backend`; on a checkout without sentence-transformers it is the engine's deterministic hashing fallback, not a neural encoder. |
| `hybrid` | MemoryStore.hybrid -> recall_hybrid (alpha=0.5) | yes | yes | RRF fusion of vector + BM25 with cross-encoder reranking ON (default). |
| `hybrid-rerank-off` | MemoryStore.hybrid, USE_CROSS_ENCODER=False | yes | yes | Same fusion with reranking disabled (MEM20_RERANK=0). A real operational configuration, not a synthetic variant. |
| `graph` | MemoryStore.graph -> recall_graph | yes | yes | Entity/edge traversal. Scored on `multi_hop` (the start entity's own fact) and `graph_hop` (an attribute node one hop away, e.g. a country's region), so n is larger than the multi_hop count alone. Only entity-bearing probes are scored; that is a corpus property, not a skip. |
| `keyword` | MemoryStore.hybrid(alpha=0.0) -> BM25 half | yes | yes | Retained for continuity with the previously published table. It is the shipped path for the sparse half but still pays the fusion wrapper, which is why `bm25` is reported separately. |
| `constant` | control retriever (ignores the query) | yes | yes | ADVERSARIAL CONTROL. Returns one fixed document that matches no corpus record. Every metric must read exactly 0.000; any non-zero value means the metric is handing out free hits. |
| `recall` | MemoryStore.recall (topic/tags filter) | yes | yes | Metadata filter, not a ranker. Scored on `recall` probes whose query IS the filter (topic family), so a filter that ignores the topic fails. Previously unscored for want of a probe class; that class now exists. |
| `recall_at` | MemoryStore.recall_at (bi-temporal) | yes | yes | Point-in-time read. Scored on `recall_at` probes: a positive instant after ingestion must return the record, and a negative instant before ingestion must return nothing. The negative half is what catches a read that ignores `as_of`. |
| `entities` | MemoryStore.entities (enumeration) | yes | yes | Query-free enumeration, ordered by degree. Scored on `entities` probes that name a high-degree node the top-k must surface. Hit rate is defined here as 'the named node is in the enumeration', not as a ranked retrieval metric. |
| `ledger` | MemoryStore.ledger (append-only tail) | yes | yes | Append-only tail, ordered not ranked. Scored on `ledger` probes that assert a known recent write is present in the tail. This measures tail ordering and completeness, not retrieval quality. |

**11 of 11 declared modes scored in this run; 11 are scoreable by this harness.** The remaining 0 are listed with their blocker rather than omitted.

## Latency

| Mode | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| `bm25` | 310 | 5.2 | 20.3 | 30.2 | 37.0 |
| `vector` | 310 | 6.8 | 23.3 | 47.2 | 60.2 |
| `hybrid` | 310 | 12.5 | 39.8 | 62.8 | 65.0 |
| `hybrid-rerank-off` | 310 | 12.5 | 42.5 | 63.1 | 75.3 |
| `graph` | 90 | 15.7 | 35.7 | 59.9 | 73.0 |
| `keyword` | 310 | 12.6 | 33.8 | 58.8 | 64.8 |
| `constant` | 310 | 0.0 | 0.0 | 0.0 | 0.0 |
| `recall` | 30 | 2.8 | 14.2 | 41.6 | 41.6 |
| `recall_at` | 30 | 2.9 | 3.1 | 9.0 | 9.0 |
| `entities` | 20 | 199.5 | 227.7 | 251.4 | 251.4 |
| `ledger` | 20 | 2.5 | 2.5 | 2.5 | 2.5 |

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
| Queries reporting a drift diagnostic | 310 | — |
| All reported healthy | True | True |

## Environment

- Python 3.11.15 on Linux-7.0.0-42-generic-x86_64-with-glibc2.36 (x86_64)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Embedder backend actually used: `hashing-fallback` — NOT a neural encoder. The vector and hybrid rows above measure this backend, not all-MiniLM-L6-v2.
- Vector deps available: True; BM25: True; cross-encoder: False

## Notes

- Scores are NOT comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR. Those run on different corpora (two of them private or vendor-defined) with different metrics. These numbers describe this corpus only.
- NO LoCoMo RESULT IS CLAIMED. This harness has not been run against the LoCoMo originals (10 conversations, 1,986 QA), so no LoCoMo figure appears in this report and none may be quoted from it. The caveat stays until a run on the originals lands.

## Reproduce

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    -k 5 --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant,recall,recall_at,entities,ledger \
    --out benchmarks/results
```

The run uses an isolated store, ingests the corpus through the engine's own ledger and index build paths, and never touches live data.
