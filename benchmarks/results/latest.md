# mem20 retrieval benchmarks

Corpus `mem20-scale-corpus-v2` — 700 grounded facts, 1300 simulated facts, 250 queries.

> [!IMPORTANT]
> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here refutes or reproduces them. These results describe this corpus only.

> [!WARNING]
> **No LoCoMo result is claimed.** This harness has not been run against the LoCoMo originals (10 conversations, 1,986 QA). No LoCoMo figure appears in this report and none may be quoted from it. The caveat stays until a run on the originals lands.

## Retrieval quality

Every row below names the dataset version and the exact command that produced it, so a number can be traced back to a reproducible run rather than to a report.

- Dataset: `mem20-scale-corpus-v2` (sha256 `c7031ab7ac08…`, 2000 records, 250 probes)
- Run command: `mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk --k 5 --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant --out benchmarks/results`
- Canonical script: `benchmarks/run-7modes.sh` (the command above, parameterised; every row below names it)
- Commit: `a9860b955fb8c8b2cadab7adbda4295693a281c9`; k=5; embedding threads=1

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms | Dataset | Run command |
|---|---|---:|---:|---:|---:|---:|---|---|
| `bm25` | adversarial | 60 | 0.767 | 0.592 | 0.000 | 5.2 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `bm25` | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 5.1 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `bm25` | contradiction | 40 | 0.050 | 0.030 | 0.000 | 5.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `bm25` | direct | 60 | 1.000 | 1.000 | 0.000 | 4.8 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `bm25` | multi_hop | 30 | 0.800 | 0.800 | 0.000 | 4.9 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `bm25` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 5.1 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `constant` | adversarial | 60 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `constant` | adversarial_hard | 40 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `constant` | contradiction | 40 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `constant` | direct | 60 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `constant` | multi_hop | 30 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `constant` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 0.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `graph` | multi_hop | 30 | 0.033 | 0.033 | 0.000 | 14.2 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid` | adversarial | 60 | 0.167 | 0.167 | 0.000 | 168.5 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid` | adversarial_hard | 40 | 0.050 | 0.050 | 0.000 | 169.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid` | contradiction | 40 | 1.000 | 0.988 | 0.000 | 166.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid` | direct | 60 | 1.000 | 0.978 | 0.000 | 148.2 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid` | multi_hop | 30 | 0.533 | 0.533 | 0.000 | 167.4 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 183.7 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | adversarial | 60 | 0.650 | 0.633 | 0.000 | 25.6 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | adversarial_hard | 40 | 0.625 | 0.515 | 0.000 | 24.3 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | contradiction | 40 | 1.000 | 0.546 | 0.000 | 25.1 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | direct | 60 | 1.000 | 0.979 | 0.000 | 25.5 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | multi_hop | 30 | 1.000 | 0.929 | 0.000 | 24.8 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `hybrid-rerank-off` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 25.6 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `keyword` | adversarial | 60 | 0.167 | 0.167 | 0.000 | 173.5 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `keyword` | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 166.9 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `keyword` | contradiction | 40 | 0.125 | 0.108 | 0.000 | 169.9 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `keyword` | direct | 60 | 1.000 | 0.983 | 0.000 | 155.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `keyword` | multi_hop | 30 | 0.467 | 0.467 | 0.000 | 159.9 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 183.7 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `vector` | adversarial | 60 | 0.667 | 0.608 | 0.000 | 18.5 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `vector` | adversarial_hard | 40 | 0.750 | 0.583 | 0.000 | 17.8 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `vector` | contradiction | 40 | 1.000 | 1.000 | 0.000 | 19.0 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `vector` | direct | 60 | 0.900 | 0.864 | 0.000 | 17.9 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `vector` | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 18.9 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |
| `vector` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 20.1 | `mem20-scale-corpus-v2@c7031ab7ac08` | `benchmarks/run-7modes.sh` |

### Adversarial control

`constant` ignores the query and always returns one fixed document that matches no corpus record. Every metric below must read exactly **0.000**; a non-zero value means the metric is handing out free hits.

| Query kind | n | Hit rate | MRR |
|---|---:|---:|---:|
| adversarial | 60 | 0.000 | 0.000 |
| adversarial_hard | 40 | 0.000 | 0.000 |
| contradiction | 40 | 0.000 | 0.000 |
| direct | 60 | 0.000 | 0.000 |
| multi_hop | 30 | 0.000 | 0.000 |
| unanswerable | 20 | 0.000 | 0.000 |

## Mode surface

Every retrieval mode present in the tree, whether this run scored it, and — where it did not — the reason. A mode is never dropped from this table: an absent row reads as "not run", which is a different and weaker statement than "blocked and documented".

| Mode | Surface | Scored | In this run | Note |
|---|:--:|:--:|:--:|---|
| `bm25` | engine BM25 index (rank_bm25), vector half never called | yes | yes | Pure sparse retrieval. Reads the engine's own bm25_index.pkl / bm25_corpus.jsonl, so it measures the index the store built. NOT the same as `keyword`: hybrid(alpha=0.0) still executes the vector half and fuses it, so calling that BM25 overstates what was isolated. |
| `vector` | MemoryStore.semantic -> recall_semantic (FAISS) | yes | yes | Dense MiniLM retrieval. ALIAS of `semantic`, not a second system: same code path, scored under the name the surface list uses. |
| `hybrid` | MemoryStore.hybrid -> recall_hybrid (alpha=0.5) | yes | yes | RRF fusion of vector + BM25 with cross-encoder reranking ON (default). |
| `hybrid-rerank-off` | MemoryStore.hybrid, USE_CROSS_ENCODER=False | yes | yes | Same fusion with reranking disabled (MEM20_RERANK=0). A real operational configuration, not a synthetic variant. |
| `graph` | MemoryStore.graph -> recall_graph | yes | yes | Entity/edge traversal. Only multi_hop probes carry an entity, so n is smaller than the text modes; that is a corpus property, not a skip. |
| `keyword` | MemoryStore.hybrid(alpha=0.0) -> BM25 half | yes | yes | Retained for continuity with the previously published table. It is the shipped path for the sparse half but still pays the fusion wrapper, which is why `bm25` is reported separately. |
| `constant` | control retriever (ignores the query) | yes | yes | ADVERSARIAL CONTROL. Returns one fixed document that matches no corpus record. Every metric must read exactly 0.000; any non-zero value means the metric is handing out free hits. |
| `recall` | MemoryStore.recall (topic/tags filter) | **no** | no | NOT SCORED: no _run_mode branch and no corpus query kind answerable by metadata filter alone. Needs a new probe class, not a reporting change. |
| `recall_at` | MemoryStore.recall_at (bi-temporal) | **no** | no | NOT SCORED: the corpus carries no as-of anchor, so there is no gold record to check a point-in-time answer against. |
| `entities` | MemoryStore.entities (enumeration) | **no** | no | NOT SCORED: query-free enumeration has no expected-evidence target, so hit rate is not a defined metric for it. |
| `ledger` | MemoryStore.ledger (append-only tail) | **no** | no | NOT SCORED: not a ranked retriever. Out of scope for hit-rate scoring by construction; belongs under a durability test. |

**7 of 11 declared modes scored in this run; 7 are scoreable by this harness.** The remainder are listed with their blocker rather than omitted.

## Latency

| Mode | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| `bm25` | 250 | 5.1 | 13.4 | 34.4 | 159.3 |
| `constant` | 250 | 0.0 | 0.0 | 0.0 | 0.0 |
| `graph` | 30 | 14.2 | 160.3 | 180.1 | 180.1 |
| `hybrid` | 250 | 166.9 | 202.7 | 278.9 | 307.1 |
| `hybrid-rerank-off` | 250 | 25.3 | 60.9 | 172.1 | 203.1 |
| `keyword` | 250 | 166.2 | 202.5 | 308.1 | 335.8 |
| `vector` | 250 | 18.5 | 50.9 | 65.8 | 204.4 |

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
| Queries reporting a diagnostic | 1530 | — |
| All reported healthy | True | True |

## Environment

- Python 3.11.15 on Linux-6.8.0-87-generic-x86_64-with-glibc2.36 (x86_64)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Vector deps available: True; BM25: True; cross-encoder: True

## Notes

- Scores are NOT comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR. Those run on different corpora (two of them private or vendor-defined) with different metrics. These numbers describe this corpus only.
- NO LoCoMo RESULT IS CLAIMED. This harness has not been run against the LoCoMo originals (snap-research/locomo, 10 conversations / 1,986 QA), so no LoCoMo figure appears in this report and none may be quoted from it. The caveat stays until a run on the originals lands.

## Reproduce

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant \
    --out benchmarks/results
```

The run uses an isolated store, ingests the corpus through the engine's own ledger and index build paths, and never touches live data.