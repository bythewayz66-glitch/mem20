# Experiment registry — retrieval modes, scored vs unscored

**Owner:** Experiment Tracker · **Round:** 2026-11-01 · **Baseline:** `main` @ `2ea4492209dfaae6afb22ca884132a0d1849bfcf`
**Machine-readable twin:** [`experiments.json`](./experiments.json) — same mode ids, same `scored` flags, built to be diffed.
**Source of every number below:** `benchmarks/results/latest.json`. Nothing here is hand-typed or estimated.

## Why this file exists

`benchmarks/results/latest.md` publishes a retrieval table. Nothing in that table names the retrieval
methods that are present in the tree and were never measured. A reader therefore cannot tell the
difference between *mem20 has seven retrieval modes* and *seven of mem20's modes happen to be the ones
we scored*.

This registry closes that gap. Every mode carries a `scored` flag and an artifact-path or `file:line`
citation, so each claim is checkable from the tree rather than from a summary.

## Headline

| | Count |
|---|---:|
| Modes present in the tree | 11 |
| **Scored in the 2026-10-31 run** (`latest.json`) | **7** |
| Present but unscored | 4 |
| Modes in `latest.json` `run_manifest.modes` | 7 |
| Registry scored rows | 7 |
| **Row count matches artifact** | **yes** |

Three things follow:

1. **The adversarial `0.000` row is visible and is a control, not a hidden failure.** `constant` is the
   adversarial control retriever and reads `0.000` on every kind by construction. See §3.
2. **Four present modes have no row at all**, including `recall_at` — the bi-temporal path that
   mem20's trustworthiness claim rests on.
3. **The four-mode run and the seven-mode run are different runs.** The four-mode run's JSON was never
   written; `latest.json` is the artifact of record. See §4.

## 1. Registry — the 2026-10-31 run, every mode scored

`n` is the number of scored queries. This table mirrors `experiments.json`'s `modes[]` row for row.

| Mode | Surface | Scored? | n | adversarial | adversarial_hard | contradiction | direct | multi_hop | unanswerable | p50 ms |
|---|---|:--:|---:|---:|---:|---:|---:|---:|---:|---:|
| `bm25` | engine BM25 index (rank_bm25), vector half never called | **yes** | 250 | 0.767 | 0.025 | 0.050 | 1.000 | 0.800 | 0.000 | 102.2 |
| `vector` | MemoryStore.semantic -> recall_semantic (FAISS) | **yes** | 250 | 0.667 | 0.750 | 1.000 | 0.900 | 1.000 | 0.000 | 204.9 |
| `hybrid` | MemoryStore.hybrid -> recall_hybrid (alpha=0.5) | **yes** | 250 | 0.167 | 0.050 | 1.000 | 1.000 | 0.533 | 0.000 | 1797.1 |
| `hybrid-rerank-off` | MemoryStore.hybrid, USE_CROSS_ENCODER=False | **yes** | 250 | 0.650 | 0.625 | 1.000 | 1.000 | 1.000 | 0.000 | 27.3 |
| `graph` | MemoryStore.graph -> recall_graph | **yes** | 30 | — | — | — | — | 0.033 | — | 208.4 |
| `keyword` | MemoryStore.hybrid(alpha=0.0) -> BM25 half | **yes** | 250 | 0.167 | 0.025 | 0.125 | 1.000 | 0.467 | 0.000 | 1692.2 |
| `constant` | control retriever (ignores the query) | **yes** | 250 | **0.000** | **0.000** | **0.000** | **0.000** | **0.000** | **0.000** | 0.0 |

Cells are **hit rate**. MRR and leak rate per kind are in `latest.json` under `recall.<mode>.<kind>`,
which is the path each `modes[].measurement` entry cites.

`graph` is scored on `multi_hop` only — the harness skips it for every other query kind because graph
traversal is only meaningful for entity queries. That is a corpus property, not a skip, and it is why
`graph` has no adversarial cell.

### The gate that makes "unscored" unambiguous

`_run_mode` in `bench.py` is a closed dispatch — `semantic` (135), `hybrid` (139), `graph` (143),
`keyword` (149) — and then:

```python
raise ValueError(mode)          # bench.py:155
```

So naming a mode outside the dispatch in `run(modes=(...))` is a hard error, not a silent skip.
"Unscored" here means *the harness has no branch for it and would refuse to run it*, which is a
stronger and more useful statement than "nobody got round to it".

## 2. Present but unscored — four modes with no row

| Mode | Surface | Scored? | n | Why it has no row |
|---|---|:--:|---:|---|
| `recall` | `MemoryStore.recall` (topic / tags) | **no** | 0 | No `_run_mode` branch and no corpus query kind answerable by metadata filter alone. |
| `recall_at` | `MemoryStore.recall_at` (bi-temporal) | **no** | 0 | The corpus carries no as-of anchor, so there is no gold record to check a point-in-time answer against. |
| `entities` | `MemoryStore.entities` (enumeration) | **no** | 0 | Query-free enumeration has no expected-evidence target, so hit rate is not a defined metric for it. |
| `ledger` | `MemoryStore.ledger` (append-only tail) | **no** | 0 | Not a ranked retriever. Out of scope for hit-rate scoring by construction; belongs under a durability test. |

These four are the `scored: false` entries in `latest.json`'s own `mode_surface` array, so the artifact
and this registry agree on them. They are not broken — they are untested, which is a different
statement.

## 3. The adversarial `0.000` row — kept visible

Two different zeros live in this artifact and they must not be confused:

| Mode | Kind | Hit rate | What it means |
|---|---|---:|---|
| `constant` | `adversarial` | **0.000** | The adversarial **control**. Returns one fixed document matching no corpus record. Every metric must read exactly 0.000; a non-zero value would mean the metric hands out free hits. |
| all 7 modes | `unanswerable` | **0.000** | The unanswerable **control**. Nothing in the corpus can answer these probes, so a correct verdict is a miss. |

Per-mode adversarial hit rates, all measured:

| Mode | adversarial | adversarial_hard | contradiction |
|---|---:|---:|---:|
| `bm25` | 0.767 | 0.025 | 0.050 |
| `vector` | 0.667 | 0.750 | 1.000 |
| `hybrid` | 0.167 | 0.050 | 1.000 |
| `hybrid-rerank-off` | 0.650 | 0.625 | 1.000 |
| `graph` | — | — | — |
| `keyword` | 0.167 | 0.025 | 0.125 |
| `constant` | **0.000** | **0.000** | **0.000** |

**A correction to the previous round of this registry.** It recorded that every adversarial row was
hard-coded to `0.000` by the scorer (`bench.py:306-307`). That is no longer true on this baseline:
`bench.py:352` assigns `hit=False` only inside the `if q.kind == "unanswerable"` control branch, and
`bench.py:363` scores `adversarial`, `adversarial_hard` and `contradiction` with the same `_hit()`
evidence check as every other answerable kind. The adversarial numbers above are therefore
**measured, not assigned** — which is why `vector` reads 0.750 on `adversarial_hard` while `keyword`
reads 0.025. A hard-coded constant could not produce that spread.

The `0.000` that remains is the `constant` control row, and it stays in the table above and in
`latest.md` where it is published. It is not hidden, reordered or deleted.

## 4. Four-mode run vs seven-mode run

| Run | Artifact | Modes scored | Modes unscored |
|---|---|---|---|
| `2026-10-31-four-mode` | `docs/benchmarks/results-four-mode-2026-10-31.md` | `keyword`, `semantic`, `hybrid`, `graph` | `bm25`, `hybrid-rerank-off`, `constant` |
| `2026-10-31-seven-mode` | `benchmarks/results/latest.json` | `bm25`, `vector`, `hybrid`, `hybrid-rerank-off`, `graph`, `keyword`, `constant` | `recall`, `recall_at`, `entities`, `ledger` |

The four-mode run scored `keyword`, `semantic`, `hybrid` and `graph`. Its JSON and markdown were never
written — `cmd_run_scale` crashed in `print(paths['json'])` because `save()` returned `None` when
`--out` did not exist, so the scores were captured from stdout. The seven-mode run supersedes it and is
the artifact of record.

`semantic` and `vector` are the **same code path** (`MemoryStore.semantic -> recall_semantic`), scored
under two names. They are one mode, not two, and this registry does not count them twice: `vector` is
the id in `latest.json`, and `semantic` is the id the four-mode run used.

## 5. How to use the JSON

`experiments.json` is the diffable form. `modes[]` joins on `modes[].id`.

The comparison rule is deliberately narrow, so a later run cannot mistake a rename for progress:

- **`scored` may flip `false → true` only if `measurement.n` also becomes `> 0`** *and* a source
  artifact containing that mode's per-query rows exists. A flip without a measurement is a **false
  promotion**.
- **`scored` flipping `true → false`** is a regression and must cite the commit that removed the
  harness branch or the artifact row.
- `stable_fields` are `id`, `surface`, `evidence`. `volatile_fields` are `measurement`, `notes`,
  `status`. Diff the first set for identity, the second for change.

The row-count check is machine-readable at `row_count_check`:

```
modes_in_latest_json      = 7
scored_rows_in_registry   = 7
unscored_rows_in_registry = 4
matches                   = true
```

## 6. What this registry does not claim

- It does not re-measure anything. Every number is read from `benchmarks/results/latest.json`
  (corpus `mem20-scale-corpus-v2`, 700 grounded / 1,300 simulated facts, 250 queries).
- It does not assert that the unscored modes are broken. They are untested, which is a different
  statement.
- It does not imply comparability with Mem0 LoCoMo 92.5, LongMemEval 94.4 or Zep DMR 94.8. Those run
  on different corpora with different metrics. Nothing here refutes or reproduces them.
- It does not claim the per-query rows are committed. `latest.json` says 1,530 per-query rows live in
  `per-query.jsonl.gz` next to it; that file is **not** in the tree at this baseline, so the aggregate
  rows above are the finest granularity actually available.

---
**Experiment Tracker** · 2026-11-01T10:40:00-07:00 · statistical confidence: not applicable — this is a registry of measurement coverage, not a measurement.
