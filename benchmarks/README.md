# Retrieval benchmarks — corpus, runner, results — `benchmarks/`

The published benchmark surface: two versioned corpora, a 7-mode runner, a
scorer, and the results that are quoted elsewhere in the repo.

**20 tracked file(s).**

## Contents

### Scale corpus v2 — the artifact of record for the published table

- `corpora/mem20-scale-corpus-v2.manifest.json` — corpus manifest (700 grounded facts, 1300 simulated facts, 250 queries)
- `corpora/mem20-scale-corpus-v2.validation.json` — corpus validation record
- `run-7modes.sh` — run all seven retrieval modes
- `score_mode.py` — score one mode
- `merge_mode_slices.py` — merge per-mode slices into one table
- `render_latest_md.py` — render `results/latest.md` from `results/latest.json`
- `results/latest.md` / `results/latest.json` — the current published results

### Scale corpus v3 — the ~100 MB load-test corpus

- `corpora/v3/manifest.json` — counts, bytes, schema, sha256 of every file and reference input
- `corpora/v3/probes.jsonl` — 600 probes with gold keys and expected evidence
- `corpora/v3/results.json` — raw probe scores
- `corpora/v3/validation.json` — validator report
- `v3/README.md` — measured numbers, category design, engine defects found
- `v3/build_corpus_v3.py` — seeded generator
- `v3/validate_corpus_v3.py` — validator (fails the build, not warns)
- `v3/load_corpus_v3.py` — loader, `--mode api` / `--mode ledger`, `--dry-run`
- `v3/score_probes_v3.py` — probe scorer
- `v3/make_manifest_v3.py` — manifest + checksums

The v3 record shards (`records.part-01..03.jsonl`, 122,178 records /
101,090,449 bytes) are **not committed** — the repo gitignores `*.jsonl`. They
regenerate byte-identically from the committed seed and the hashed reference
cache under `reference/v3/`.

## Usage

```bash
# v2 — the published 7-mode table
bash benchmarks/run-7modes.sh
python3 benchmarks/score_mode.py
python3 benchmarks/render_latest_md.py --check   # drift gate

# v3 — the ~100 MB load-test corpus
python benchmarks/v3/build_corpus_v3.py --per-category 30000 --out benchmarks/corpora/v3
python benchmarks/v3/validate_corpus_v3.py benchmarks/corpora/v3
```

## Notes

**These numbers are not comparable to competitor benchmarks.** The corpora are
mem20's own; Mem0's LoCoMo/LongMemEval and Zep's DMR figures come from different
corpora and metrics. No LoCoMo result is claimed — the harness has not been run
against the LoCoMo originals. Keep that caveat attached to any quoted number.

`results/latest.md` is a **view** of `results/latest.json`, not a second source
of truth. Regenerate it with `render_latest_md.py`; `--check` fails if the two
drift.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
