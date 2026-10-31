# Experiment registry — retrieval modes, scored vs unscored

**Owner:** Experiment Tracker · **Round:** 2026-10-27 · **Baseline:** `main` @ `45445f4850377814cd95b7fa50c0a9153f76c163`
**Machine-readable twin:** [`experiments.json`](./experiments.json) — same mode ids, same `scored` flags, built to be diffed.

## Why this file exists

`benchmarks/results/latest.md` publishes a retrieval table with four modes in it: `graph`, `hybrid`, `keyword`, `semantic`. Nothing in that table, and nothing in `docs/benchmarks/results-v1.json`, names the retrieval methods that are present in the tree and were never measured. A reader of the benchmark page therefore cannot tell the difference between *mem20 has four retrieval modes* and *four of mem20's modes happen to be the ones we scored*.

This registry closes that gap. Every mode below carries a `scored` flag and a `file:line` citation, so each claim is checkable from the tree rather than from a summary.

## Headline

| | Count |
|---|---:|
| Modes present in the tree | 13 |
| Scored — standalone hit-rate/MRR rows | 4 |
| Scored — as a variant of another mode | 1 |
| Present but unscored | 8 |
| Adversarial rows in the published artifact | 9 |
| Adversarial hit rate (at baseline) | **0.000 — was structurally assigned, not measured** — since fixed, see §3 |

Three things follow, and they are the reason for this task:

1. **The adversarial `0.000` was not a measurement.** At the baseline SHA, `bench.py` assigned `hit=False, rank=None` to every adversarial query unconditionally. That branch has since been removed — see §3, which is retained as the record of the defect.
2. **Eight present modes have no row at all**, including `recall_at` — the bi-temporal path that mem20's trustworthiness claim rests on.
3. **The published headline hit rates are depressed by the structural zero.** `hybrid`, `keyword` and `semantic` all show `0.692308`; their answerable-only hit rate is `0.900`.

## 1. Registry — every mode, scored or not

`n` is the number of scored queries. "Answerable-only" excludes the adversarial rows, because those are the ones the scorer overrides. The JSON's `modes[]` array is the authoritative list; this table mirrors it row for row.

| Mode | Surface | Scored? | n | Answerable hit | Answerable MRR | Evidence |
|---|---|:--:|---:|---:|---:|---|
| `graph` | `MemoryStore.graph` → `recall_graph` | **yes** | 2 | 1.000 | 1.000 | `bench.py:130`, `bench.py:291`, `api.py:310`, `memory.py:1448` |
| `hybrid` | `MemoryStore.hybrid` → `recall_hybrid` | **yes** | 13 | 0.900 | 0.820 | `bench.py:126`, `bench.py:248`, `api.py:293`, `memory.py:3683` |
| `keyword` | `hybrid(alpha=0.0)` → BM25 half | **yes** | 13 | 0.900 | 0.820 | `bench.py:136`, `bench.py:248`, `METHOD_MANIFEST.json` n=4 |
| `semantic` | `MemoryStore.semantic` → `recall_semantic` | **yes** | 13 | 0.900 | 0.850 | `bench.py:122`, `api.py:272`, `memory.py:3583` |
| `cross_encoder_rerank` | `retrieval_v2.rerank` inside hybrid | **variant** | 26 | — | see §2 | `bench.py:337`, `bench.py:346`, `retrieval_v2.py:259` |
| `recall` | `MemoryStore.recall` (topic/tags) | **no** | 0 | — | — | `api.py:263`, `memory.py:779`, `bench.py:142`, `results-v1.json` |
| `recall_at` | `MemoryStore.recall_at` (bi-temporal) | **no** | 0 | — | — | `api.py:268`, `memory.py:818`, `results-v1.json` |
| `entities` | `MemoryStore.entities` | **no** | 0 | — | — | `api.py:317`, `results-v1.json` |
| `ledger` | `MemoryStore.ledger` | **no** | 0 | — | — | `api.py:329`, `results-v1.json` |
| `memory_shared_recall` | MCP tool, namespace + ACL | **no** | 0 | — | — | `mcp/memory_tools.py:845`, `:1867`, `mcp/server.py:471` |
| `memory_probe` | MCP tool, entity probe | **no** | 0 | — | — | `mcp/memory_tools.py:373`, `:963`, `mcp/server.py:356` |
| `memory_related` | MCP tool, adjacent entities | **no** | 0 | — | — | `mcp/memory_tools.py:418`, `:2174`, `mcp/server.py:529` |
| `memory_reason` | MCP tool, multi-entity reasoning | **no** | 0 | — | — | `mcp/memory_tools.py:386` |

Paths are relative to the repo root. Line numbers are as of the baseline SHA above.

### The gate that makes "unscored" unambiguous

`_run_mode` in `bench.py` is a closed dispatch — `semantic` (122), `hybrid` (126), `graph` (130), `keyword` (136) — and then:

```python
raise ValueError(mode)          # bench.py:142
```

So naming a fifth mode in `run(modes=(...))` is a hard error, not a silent skip. "Unscored" here means *the harness has no branch for it and would refuse to run it*, which is a stronger and more useful statement than "nobody got round to it".

## 2. The one real ablation in the tree

`cross_encoder_rerank` is the only experiment with a genuine control arm and a contrast that was pre-registered rather than fitted after the fact. `bench.py:337` measures hybrid with and without reranking; `bench.py:346` toggles `engine.USE_CROSS_ENCODER` and re-runs the hybrid arm both ways.

| Arm | p50 ms | direct MRR | multi-hop MRR | direct hit | multi-hop hit |
|---|---:|---:|---:|---:|---:|
| Rerank on (default) | 101.36 | 1.000 | 0.640 | 1.000 | 0.800 |
| Rerank off | 15.73 | 0.900 | 0.800 | 1.000 | 0.800 |

**Reading it honestly:** reranking buys +0.10 direct MRR, loses 0.16 multi-hop MRR, and costs 6.4× latency. It is a trade, not an improvement — and the current default-on setting is the wrong side of that trade for multi-hop workloads. This is the strongest causal claim available from the artifacts, and it is about a *modifier*, not about any retrieval mode's quality.

One caveat that limits it: `METHOD_MANIFEST.json` carries open defect **CE-1** — the `memory.py` recompute block computes cross-encoder scores and lets none reach the output. The working implementation is `retrieval_v2.rerank`. So the "on" arm may be measuring a partially inert code path.

## 3. The adversarial zero is structural — **RESOLVED**

> **Status: fixed.** This section describes the defect as it stood at the
> baseline SHA. The `if q.kind == "adversarial": hit, rank = False, None` branch
> no longer exists. `bench.py` now routes every answerable kind — `direct`,
> `multi_hop`, `adversarial`, `adversarial_hard`, `contradiction` — through the
> same `_hit()` evidence check, and the only remaining constant is the
> `unanswerable` **control** (`bench.py:352`), which is a separate kind precisely
> so a hardcoded verdict cannot masquerade as a measurement again. The
> `adversarial` / `adversarial_hard` / `contradiction` rows in
> `benchmarks/results/latest.md` are now observed values. The analysis below is
> kept as the record of what was wrong and why it mattered.

At the baseline, every adversarial row in `benchmarks/results/latest.md` read `0.000`. That number was **assigned, not observed**:

```python
if q.kind == "adversarial":
    hit, rank = False, None     # bench.py:307 — unconditional (REMOVED)
    leaked = _leak(hits, sim_markers)
```

Retrieval was never consulted for `hit`. Three consequences:

**It cannot regress.** An invariant of the scorer does not detect anything, so no future code change, corpus or index state can move it. It is not a signal.

**It is contradicted by the rows themselves.** All nine adversarial entries in `latest.json` record `n_results = 5`. Retrieval returned five results every time; a retrieval failure could not do that. The zero belongs to the scorer.

**It distorts the published headline.** The table averages the three zeroed rows into each mode's hit rate:

| Mode | Published hit rate | Answerable-only | Denominator effect |
|---|---:|---:|---:|
| `hybrid` | 0.692308 | 0.900 | 3 of 13 rows are structural zeros |
| `keyword` | 0.692308 | 0.900 | 3 of 13 |
| `semantic` | 0.692308 | 0.850 MRR | 3 of 13 |
| `graph` | 1.000000 | 1.000 | 0 — graph never gets an adversarial row |

`graph`'s `1.000` and `hybrid`'s `0.692` are not comparable, because graph is scored on a different question set. That is a presentation defect in the table, not a retrieval result.

**What *is* measured adversarially:** `leak_rate`, which tests whether simulated content came back — 0.000 across all three modes, 3 queries each. That is a real measurement of the grounded/simulated partition, and it is *narrower* than abstention. The trust gate checks only this (`cli.py:66`), so an adversarial hit-rate regression could never fail a build.

**What to measure instead:** whether the top-k contains grounded evidence for an adversarial query — i.e. abstention precision. The per-query `n_results` field already exists to build on.

## 4. Unscored experiments

Four things in the tree are experiments that never produced a committed result. None may be quoted as a measurement.

| Experiment | Status | Why it is not a number |
|---|---|---|
| `scale-corpus-2000` | code only | `run-scale` exists (`cli.py:246`) and defaults to `keyword,semantic,hybrid`, silently dropping `graph` at scale — but branch `feat/scale-corpus-2000` carries no results directory. |
| `qa5000` | scaffold | `bench/qa5000/README.md` states no questions have been executed and the results table ships empty. |
| `bench/eval_rerank.py` | non-reproducible | Hard-codes a private bench store outside the repo and wires only `semantic` and `hybrid` (`:61-63`) — a strict subset of the main harness, with no committed artifact. |
| environment re-run | blocked | See below. |

### Can the published numbers be recomputed from a clean clone?

Partially, and the failure is informative. With `numpy` and `rank_bm25` present but no embedding stack, seeding the 14-fact corpus leaves the store **unhealthy** because the vector index is absent:

```
vector: {"present": false, "healthy": false}
bm25:   {"indexed": 14, "missing_from_ledger": 0, "healthy": true}
graph:  {"entities": 38, "edges": 70, "facts_referenced": 14, "healthy": true}
```

`cmd_run` refuses to publish from an unhealthy store (exit 2), which is correct behaviour. Reproducing the table therefore requires the exact environment the artifact records: Python 3.14.6, `sentence-transformers/all-MiniLM-L6-v2` (384-dim), plus the cross-encoder. Anyone quoting these numbers should state that they depend on that environment.

## 5. Gaps, in the order they matter

| # | Gap | Blocks | Evidence |
|---|---|---|---|
| G1 | ~~Adversarial hit rate is hard-coded to 0.000~~ — **resolved**; only the `unanswerable` control is constant now | Any abstention claim | `bench.py:352` |
| G2 | `recall_at` (bi-temporal) has no row | The trustworthiness differentiator | `api.py:268` |
| G3 | `graph` has n=2 | Graph quality claim | `latest.json` `recall.graph.multi_hop.n` |
| G4 | Four MCP retrieval tools unreachable from harness | `memory_probe`, `memory_related`, `memory_shared_recall`, `memory_reason` | `mcp/memory_tools.py:373,418,845,386` |
| G5 | No gate keeps this registry current | The next false "scored" claim | `cli.py:55-70` |
| G6 | ~~Scale run never recorded~~ — **resolved**; `mem20-scale-corpus-v2` (2,000 records / 250 probes) is recorded in `benchmarks/results/latest.json` | Any claim above 14 facts | `benchmarks/results/latest.json` |

## 6. How to use the JSON

`experiments.json` is the diffable form. `modes[]` is sorted in a fixed order and joins on `modes[].id`.

The comparison rule is deliberately narrow, so a later run cannot mistake a rename for progress:

- **`scored` may flip `false → true` only if `measurement.n` also becomes `> 0`** *and* a source artifact containing that mode's per-query rows exists. A flip without a measurement is a **false promotion**.
- **`scored` flipping `true → false`** is a regression and must cite the commit that removed the harness branch.
- `stable_fields` are `id`, `surface`, `evidence`. `volatile_fields` are `measurement`, `notes`, `status`. Diff the first set for identity, the second for change.

Suggested check: `diff` the `scored` flags first, then the `measurement.n` values. Any disagreement between the two lists is the thing to investigate.

## 7. What this registry does not claim

- It does not re-measure anything. Every number here is copied from `docs/benchmarks/results-v1.json` (corpus `mem20-agent-kb-v1`, 14 facts / 3 simulated / 13 queries, introduced in `f505379`), or computed from its `per_query` rows. It is **not** derived from `benchmarks/results/latest.json`, which holds the `mem20-scale-corpus-v2` run and records no `per_query` rows.
- It does not assert that the unscored modes are broken. They are untested, which is a different statement, and the manifest separately records several of them as `working`.
- It does not imply comparability with Mem0 LoCoMo 92.5, LongMemEval 94.4 or Zep DMR 94.8. Those run on different corpora with different metrics. Nothing here refutes or reproduces them.

---
**Experiment Tracker** · 2026-10-27T09:30-06:00 · statistical confidence: not applicable — this is a registry of measurement coverage, not a measurement.
