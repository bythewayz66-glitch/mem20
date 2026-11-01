# Retrieval benchmarks — corpus, runner, results — `benchmarks/`

The published benchmark surface: a versioned corpus, a 7-mode runner, a scorer,
and the results that are quoted elsewhere in the repo.

**8 tracked file(s).**

## Contents

- `corpora/mem20-scale-corpus-v2.manifest.json` — corpus manifest (700 grounded facts, 1300 simulated facts, 250 queries)
- `corpora/…validation.json` — corpus validation record
- `run-7modes.sh` — run all seven retrieval modes
- `score_mode.py` — score one mode
- `merge_mode_slices.py` — merge per-mode slices into one table
- `results/latest.md` / `results/latest.json` — the current published results

## Usage

```bash
bash benchmarks/run-7modes.sh
python3 benchmarks/score_mode.py
```

## Notes

**These numbers are not comparable to competitor benchmarks.** The corpus is
mem20's own; Mem0's LoCoMo/LongMemEval and Zep's DMR figures come from different
corpora and metrics. No LoCoMo result is claimed — the harness has not been run
against the LoCoMo originals. Keep that caveat attached to any quoted number.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
