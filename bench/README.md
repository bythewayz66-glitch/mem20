# Retrieval benchmark harness — `bench/`

Offline harness that builds the retrieval corpus, generates queries, and scores
reranking. Produces the evidence files consumed by `benchmarks/`.

**24 tracked file(s).**

## Contents

- `build_index.py` — build the retrieval index over the corpus
- `extract_corpus.py` — pull grounded facts out of the store
- `make_queries.py` — generate the query set
- `eval_rerank.py` — score reranking against labels
- `label_plan*.json` / `label_applied*.json` — labelling plans and applied labels
- `ce_trace_evidence.json`, `clone_audit.json`, `clone_check.json` — captured evidence

## Usage

```bash
python3 bench/extract_corpus.py
python3 bench/build_index.py
python3 bench/make_queries.py
python3 bench/eval_rerank.py
```

## Notes

Results are written to `benchmarks/results/`. Do not hand-edit the captured
`*.json` evidence files — they are records of a specific run.

---

Part of the [mem20 monorepo](../README.md). See [`docs/INDEX.md`](../docs/INDEX.md) for the full documentation map.
