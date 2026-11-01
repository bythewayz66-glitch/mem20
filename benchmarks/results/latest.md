# mem20 retrieval benchmarks

Corpus `mem20-scale-corpus-v2` — 700 grounded facts, 1300 simulated facts, 250 probes. Seed `20261027`.

> [!IMPORTANT]
> **These numbers are not comparable to competitor benchmarks.** Mem0's LoCoMo (92.5) and LongMemEval (94.4) figures and Zep's DMR (94.8%) come from different corpora — two of the three are private or vendor-defined — and different metrics. Nothing here refutes or reproduces them. These results describe this corpus only.

> [!NOTE]
> **No LoCoMo run exists in this repository.** This table scores mem20's own retrieval modes on mem20's own corpus. It is not a LoCoMo result and must not be quoted as one. The caveat stays until a LoCoMo run lands with its own artifact.

## Mode surface — 7 retrieval modes scored, 4 non-retrieval surfaces declared out of scope

| Mode | Surface | Scored | Scored in this run | Note |
|---|---|---:|---:|---|
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

**7 retrieval modes scored in this run.** The four that were previously unscored — `bm25`, `vector`, `graph` and `hybrid-rerank-off` — now each carry a row. The four non-retrieval surfaces below them (`recall`, `recall_at`, `entities`, `ledger`) are listed with their blocker rather than omitted: none of them is a ranked retriever, so hit rate is not a defined metric for them.

## Retrieval quality

| Mode | Query kind | n | Hit rate | MRR | Leak rate | p50 ms |
|---|---|---:|---:|---:|---:|---:|
| `bm25` | adversarial | 60 | 0.767 | 0.592 | 0.000 | 102.0 |
| `bm25` | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 101.8 |
| `bm25` | contradiction | 40 | 0.050 | 0.030 | 0.000 | 195.9 |
| `bm25` | direct | 60 | 1.000 | 1.000 | 0.000 | 101.6 |
| `bm25` | multi_hop | 30 | 0.800 | 0.800 | 0.000 | 102.7 |
| `bm25` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 149.7 |
| `vector` | adversarial | 60 | 0.667 | 0.608 | 0.000 | 203.5 |
| `vector` | adversarial_hard | 40 | 0.750 | 0.583 | 0.000 | 203.9 |
| `vector` | contradiction | 40 | 1.000 | 1.000 | 0.000 | 296.0 |
| `vector` | direct | 60 | 0.900 | 0.864 | 0.000 | 202.0 |
| `vector` | multi_hop | 30 | 1.000 | 0.950 | 0.000 | 299.6 |
| `vector` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 297.1 |
| `hybrid` | adversarial | 60 | 0.167 | 0.167 | 0.000 | 1694.7 |
| `hybrid` | adversarial_hard | 40 | 0.050 | 0.050 | 0.000 | 1897.8 |
| `hybrid` | contradiction | 40 | 1.000 | 0.988 | 0.000 | 1899.2 |
| `hybrid` | direct | 60 | 1.000 | 0.978 | 0.000 | 1691.0 |
| `hybrid` | multi_hop | 30 | 0.533 | 0.533 | 0.000 | 1799.0 |
| `hybrid` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 2003.1 |
| `hybrid-rerank-off` | adversarial | 60 | 0.650 | 0.633 | 0.000 | 25.4 |
| `hybrid-rerank-off` | adversarial_hard | 40 | 0.625 | 0.515 | 0.000 | 25.5 |
| `hybrid-rerank-off` | contradiction | 40 | 1.000 | 0.546 | 0.000 | 25.7 |
| `hybrid-rerank-off` | direct | 60 | 1.000 | 0.979 | 0.000 | 77.9 |
| `hybrid-rerank-off` | multi_hop | 30 | 1.000 | 0.929 | 0.000 | 76.4 |
| `hybrid-rerank-off` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 78.6 |
| `graph` | multi_hop | 30 | 0.033 | 0.033 | 0.000 | 208.5 |
| `keyword` | adversarial | 60 | 0.167 | 0.167 | 0.000 | 1800.1 |
| `keyword` | adversarial_hard | 40 | 0.025 | 0.006 | 0.000 | 3198.4 |
| `keyword` | contradiction | 40 | 0.125 | 0.108 | 0.000 | 2102.3 |
| `keyword` | direct | 60 | 1.000 | 0.983 | 0.000 | 1399.1 |
| `keyword` | multi_hop | 30 | 0.467 | 0.467 | 0.000 | 380.4 |
| `keyword` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 895.9 |
| `constant` | adversarial | 60 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | adversarial_hard | 40 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | contradiction | 40 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | direct | 60 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | multi_hop | 30 | 0.000 | 0.000 | 0.000 | 0.0 |
| `constant` | unanswerable | 20 | 0.000 | 0.000 | 0.000 | 0.0 |

### Aggregate per mode

| Mode | n | Hit rate | MRR | Leak rate | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| `bm25` | 250 | 0.532 | 0.484 | 0.000 | 102.2 | 299.8 |
| `vector` | 250 | 0.776 | 0.721 | 0.000 | 204.9 | 396.8 |
| `hybrid` | 250 | 0.512 | 0.505 | 0.000 | 1797.1 | 2406.3 |
| `hybrid-rerank-off` | 250 | 0.776 | 0.668 | 0.000 | 27.3 | 97.2 |
| `graph` | 30 | 0.033 | 0.033 | 0.000 | 208.4 | 2293.9 |
| `keyword` | 250 | 0.360 | 0.350 | 0.000 | 1692.2 | 3502.5 |
| `constant` | 250 | 0.000 | 0.000 | 0.000 | 0.0 | 0.0 |

`graph` covers only `multi_hop` probes (n=30) because graph traversal needs an entity; its aggregate is therefore not comparable to the text modes' n=250.

## The adversarial control — 0.000, kept visible

`constant` is a retriever that ignores the query and returns one fixed document containing no corpus vocabulary. Every metric on it must read exactly 0.000. A non-zero value would mean the metric is handing out free hits, which would invalidate every other number in this file.

| Mode | Query kind | n | Hit rate | MRR |
|---|---|---:|---:|---:|
| `constant` | adversarial | 60 | 0.000 | 0.000 |
| `constant` | adversarial_hard | 40 | 0.000 | 0.000 |
| `constant` | contradiction | 40 | 0.000 | 0.000 |
| `constant` | direct | 60 | 0.000 | 0.000 |
| `constant` | multi_hop | 30 | 0.000 | 0.000 |
| `constant` | unanswerable | 20 | 0.000 | 0.000 |

**Control verdict: PASS — all six kinds exactly 0.000.** The `unanswerable` kind is a second, independent control: nothing in the corpus can answer it, so it must also read 0.000 in every real mode. It does.

## Latency

| Mode | n | p50 ms | p95 ms | p99 ms | max ms |
|---|---:|---:|---:|---:|---:|
| `bm25` | 250 | 102.2 | 299.8 | 402.2 | 4398.5 |
| `vector` | 250 | 204.9 | 396.8 | 496.2 | 2197.0 |
| `hybrid` | 250 | 1797.1 | 2406.3 | 3398.8 | 3904.2 |
| `hybrid-rerank-off` | 250 | 27.3 | 97.2 | 197.4 | 657.3 |
| `graph` | 30 | 208.4 | 2293.9 | 2405.8 | 2405.8 |
| `keyword` | 250 | 1692.2 | 3502.5 | 4199.7 | 6097.3 |
| `constant` | 250 | 0.0 | 0.0 | 0.0 | 0.0 |

## Trustworthiness

| Check | Value | Required |
|---|---:|---|
| Contamination rate | 0.0 | 0.0 |
| Simulated records in BM25 corpus | [] | 0 |
| Stale pointer rate | 0.000000 | 0.0 |
| Index healthy | True | True |
| Ledger records | 700 | — |
| Graph entities / edges | 654 / 3601 | — |
| Queries reporting a diagnostic | 250 | — |
| All reported healthy | True | True |

## Environment

- Python 3.11.15 on Linux-6.8.0-87-generic-x86_64-with-glibc2.36 (x86_64)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim)
- Vector deps available: True; BM25: True; cross-encoder: True
- Store: `/tmp/mem20-scale-gw5m7r7d` — vector 700 entries, BM25 700, graph 654 entities / 3601 edges

## Dataset version

`mem20-scale-corpus-v2`, seed `20261027`. SHA-256 of the corpus files this run consumed:

| File | SHA-256 |
|---|---|
| `grounded.jsonl` | `bdb696ab29f5f2ed47738e53a77576d1e1a5ae8e3f6d87d2a9bd1f0e97f77d0e` |
| `simulated.jsonl` | `af958ac5d7e3a4d8f30501ab22f8435e4382a9d675968ef657ae1a11c25da65d` |
| `queries.jsonl` | `2d64afa0a1974278e2544d6fd0bca767693c7305f584f0c4eddd6b2d27e3cc4a` |
| `records.jsonl` | `28f0746be240d216ea5368eeb0babba666e90c05a67f98f32d546369dfc2dbd3` |

## Per-query rows

All 1530 per-query rows are committed verbatim in [`per-query.jsonl.gz`](per-query.jsonl.gz) — nothing is omitted. Each row carries `qid`, `kind`, `mode`, `hit`, `rank`, `leaked`, `n_results` and `latency_ms`, so every aggregate above can be recomputed from the committed data.

| Artifact | Bytes | Lines | SHA-256 |
|---|---:|---:|---|
| `per-query.jsonl.gz` (committed) | 12,677 | 1,530 | `a1e9768a89fd438b71b5d2ec3025324c6d533ae3ea9479983800a17ca07be55f` |
| `per-query.jsonl` (`gunzip -c`) | 283,255 | 1,530 | `532525aaccf1eff9c9e5faf4ff4bacafb7403a04511bcc9c7e0966e44234dc07` |

It is committed gzipped only to keep the blob reviewable; `gunzip -c benchmarks/results/per-query.jsonl.gz` reproduces the plain JSONL byte-for-byte at the SHA-256 above.

## Notes

- Scores are NOT comparable to Mem0's LoCoMo/LongMemEval or Zep's DMR. Those run on different corpora (two of them private or vendor-defined) with different metrics. These numbers describe this corpus only.
- NO LoCoMo RESULT IS CLAIMED. This harness has not been run against the LoCoMo originals (snap-research/locomo, 10 conversations / 1,986 QA), so no LoCoMo figure appears in this report and none may be quoted from it. The caveat stays until a run on the originals lands.
- `graph` at n=30 is a real measurement, not the n=2 directional figure the previous table carried. It is much lower than that figure suggested.
- `keyword` (`hybrid(alpha=0.0)`) still pays the fusion wrapper and the vector call, which is why its p50 is far above `bm25`'s. `bm25` reads the engine's own index directly and is the honest sparse number.

## Reproduce

```bash
# 1. corpus (deterministic, seed 20261027)
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2

# 2. build the store once
mem20benchmarkz ingest-scale --corpus /tmp/mem20-scale-corpus-v2 \
    --store /tmp/mem20-scale-store --bulk

# 3. score each mode against that store
for m in bm25 vector hybrid hybrid-rerank-off graph keyword constant; do
  python benchmarks/score_mode.py /tmp/mem20-scale-store \
      /tmp/mem20-scale-corpus-v2 $m /tmp/slices/$m.json
done

# 4. merge the slices into benchmarks/results/latest.json
python benchmarks/merge_mode_slices.py
```

Modes are scored in separate processes because this host caps at 2 GB and a single process that ingests and scores all seven is OOM-killed (exit 137). Every mode is scored against the same already-built store, so the numbers are comparable; only the process boundary differs.

The run uses an isolated store, ingests the corpus through the engine's own ledger and index build paths, and never touches live data.
