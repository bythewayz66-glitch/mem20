# mem20-scale-corpus-v3

A deterministic, ~100 MB load-test corpus for the mem20 memory store, split
exactly three ways into **grounded**, **ungrounded** and **false** facts, with a
600-probe retrieval set and a loader that writes through the real store API.

Everything below is measured on this machine, not estimated.

## Measured numbers

| | |
|---|---|
| records | **122,178** |
| per category | **40,726** each (exactly 1/3) |
| serialized bytes | **101,090,449** (96.41 MiB / 101.09 MB) |
| bytes per record | 827.4 |
| shards | 3 (36.7 MB, 36.7 MB, 27.7 MB) |
| probes | 600 (200 direct, 150 adversarial, 150 contradiction, 100 control) |
| seed | 20261101 |
| validator | **PASS** — 0 errors, 0 warnings, 0 duplicate keys, 0 duplicate ids |

Reproducibility was verified by generating twice and comparing sha256 of every
shard: byte-identical.

## The three categories

**grounded (40,726)** — verifiably true, transcribed from a real cached source.
Every record carries `source` (the URL) and `evidence` (the verbatim source
fields). Six families, all from public, key-free datasets:

| family | records | source |
|---|---|---|
| codepoint | 38,932 | Unicode Character Database `UnicodeData.txt` |
| city | 26,322 | GeoNames `cities15000` |
| mime | 7,912 | `jshttp/mime-db` |
| countrymeta | 3,282 | `mledoze/countries` |
| country | 2,680 | ISO-3166 (lukes) |
| element | 2,324 | PeriodicTableJSON |

**ungrounded (40,726)** — a coherent fictional universe: invented companies,
cities, roles, products and policies. Internally consistent, `source: null`,
`epistemic_status: imagined`. Nothing here is claimed to be true.

**false (40,726)** — a deterministic mutation of a grounded record: the object
is swapped for a different value from the same `(family, predicate)` pool, so
the wrong value is always the right *kind* of value. Each carries `contradicts`
(the grounded key it denies) and `true_value` (what that key actually holds).
`object` holds the **wrong** value — the claim asserts it.

The categories are never blurred. The validator fails the build if a grounded
record lacks a source, if a false record's `contradicts` target is not in the
corpus, or if a false record's own text restates the true value (a claim that
contradicts itself in the same sentence is not a false fact, it is noise).

## Retrieval results (measured, BM25 half only)

600 probes against a store loaded with all 122,178 records, `k=10`,
`alpha=0.0` (BM25 only — no vector deps installed on this host):

| probe kind | n | hit@1 | hit@5 | hit@10 | MRR |
|---|---|---|---|---|---|
| direct | 200 | 0.935 | 0.945 | 0.980 | 0.944 |
| adversarial | 150 | 0.733 | 0.853 | 0.933 | 0.787 |
| contradiction | 150 | 0.600 | 0.887 | 0.947 | 0.730 |
| **unanswerable (control)** | 100 | **0.000** | **0.000** | **0.000** | **0.000** |

The control is the important row: 100 probes about entities that do not exist
in the corpus score exactly zero, which is what proves the metric is not
handing out free hits. The control is scored as "did any returned record
mention the queried subject", not "did the store return anything" — BM25 always
returns `k` rows regardless of relevance, so the naive test would read 1.000.

These are **not** comparable to published LoCoMo / LongMemEval / DMR numbers:
those are LLM-judged end-answer accuracy on the original datasets. These are
evidence-level retrieval rates on our own synthetic corpus.

## Two engine defects found and fixed while building this

Both were found by running the corpus through the real store, not by reading
the code.

1. **`np` was only imported inside the vector try-block.** With `rank_bm25`
   installed but no `sentence-transformers`/`faiss`, `recall_hybrid` raised
   `NameError: name 'np' is not defined` at `np.argsort` — and the bare
   `except Exception: pass` around the BM25 half swallowed it. Hybrid search
   returned `[]` for every query while reporting itself as working. Fixed by
   importing numpy independently and replacing the silent `pass` with a
   warning that names the failure.

2. **BM25 tokenization kept punctuation.** Indexing and querying both used
   `text.lower().split()`, so the query token `hydrogen?` never matched the
   indexed token `hydrogen`. Every question-shaped probe missed its own record:
   direct hit@1 measured **0.292** before the fix and **0.935** after. Fixed
   with a shared `_bm25_tokens()` used by both `rebuild_bm25()` and
   `recall_hybrid()`.

## Files

| file | what |
|---|---|
| `records.part-01..03.jsonl` | the corpus, 122,178 records |
| `probes.jsonl` | 600 probes with gold keys and expected evidence |
| `manifest.json` | counts, bytes, schema, sha256 of every file and reference input |
| `validation.json` | the validator's report |
| `results.json` | the raw probe scores above |
| `benchmarks/v3/build_corpus_v3.py` | seeded generator |
| `benchmarks/v3/validate_corpus_v3.py` | validator (fails the build, not warns) |
| `benchmarks/v3/load_corpus_v3.py` | loader, `--mode api` / `--mode ledger`, `--dry-run` |
| `benchmarks/v3/score_probes_v3.py` | probe scorer |
| `benchmarks/v3/make_manifest_v3.py` | manifest + checksums |

## Reproduce

```bash
# 1. fetch the reference cache once (see reference/v3/README.md)
# 2. generate
python benchmarks/v3/build_corpus_v3.py --per-category 48000 --out benchmarks/corpora/v3
# 3. validate
python benchmarks/v3/validate_corpus_v3.py benchmarks/corpora/v3
# 4. load
python benchmarks/v3/load_corpus_v3.py benchmarks/corpora/v3 \
    --mode ledger --store /tmp/mem20-v3-store --rebuild
# 5. score
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python benchmarks/v3/score_probes_v3.py benchmarks/corpora/v3 \
    --store /tmp/mem20-v3-store --limit 0
```

## Loading notes

- `--mode ledger` appends the ledger envelopes directly and rebuilds indexes
  once. This is the only practical route at this size: `remember()` encodes one
  sentence per record (~0.5 s each), so 122k records through the API is hours.
  Measured ledger load: **~40 s** for 122,178 records.
- `--mode api` uses `mem20api.open_store()` and the real `remember()` /
  `remember_simulated()` writers. Correct, and slow by design.
- `MEM20_STORE_PATH` is resolved at import time, so the loader sets it from
  `--store` **before** importing the engine. A later assignment is silently
  ignored.
- `_append_ledger()` rotates `ledger.jsonl` into `backups/ledger_<epoch>.jsonl`
  every 2,000 lines. `wc -l ledger.jsonl` under-reports a bulk load by orders of
  magnitude — use `--count`, which sums the live ledger plus every archive.
- The firewall holds: grounded records land in `ledger.jsonl`, ungrounded and
  false in `simulated_ledger.jsonl`. Verified through the engine's own
  `_load_ledger()` / `_load_simulated_ledger()`: 40,726 / 81,452, and
  `audit_contamination()` reports `contamination_rate: 0.0`, `status: CLEAN`.
- The graph index rebuilds (55,759 entities, 418,204 edges). The vector index
  needs `sentence-transformers` + `faiss`, which are not installed here, so
  `health()` reports `healthy: false` for that one index — that is a missing
  dependency, not a corpus defect.

## Assumptions

- The record envelope is a **superset** of what mem20 writes: the engine's own
  fields plus benchmark metadata (`key`, `category`, `subject`, `predicate`,
  `object`, `contradicts`, `true_value`, `difficulty`, `provenance`). The loader
  passes only the fields each write path accepts.
- `epistemic_status` uses mem20's vocabulary: `observed` for grounded,
  `imagined` for ungrounded, `agent_generated` for false.
- Grounded facts are checkable against the cited URL as of 2026-11-01. The
  reference cache is hashed into the manifest so a re-run is reproducible for
  exactly that cache.
