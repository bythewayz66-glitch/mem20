# Benchmark corpora

| Corpus | Size | Purpose |
|--------|------|---------|
| `mem20-agent-kb-v1` | 14 facts / 13 queries | CI regression gate (in `corpus.py`) |
| `mem20-scale-corpus-v1` | **2000** facts / 40 simulated / 140 queries | Scale latency + trust |

## Generate the 2000-entry scale corpus

Nothing large is committed. Generate deterministically (seed 20):

```bash
python -m mem20benchmarkz generate-scale --out benchmarks/corpora/mem20-scale-corpus-v1
# or:
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v1
```

Produces:

- `facts.jsonl` — 2000 grounded records  
- `simulated.jsonl` — 40 adversarial-only strings  
- `queries.jsonl` — 80 direct + 40 multi_hop + 20 adversarial  
- `manifest.json`

## Ingest + run

```bash
# one-time seed (uses real remember path)
mem20benchmarkz ingest-scale \
  --corpus benchmarks/corpora/mem20-scale-corpus-v1 \
  --store /tmp/mem20-scale-store \
  --progress

# score against that store
mem20benchmarkz run-scale \
  --store /tmp/mem20-scale-store \
  --corpus benchmarks/corpora/mem20-scale-corpus-v1 \
  --out benchmarks/results-scale \
  --no-rerank-compare

# or all-in-one (temp store, in-memory 2000 facts, no JSONL on disk)
mem20benchmarkz run-scale --out benchmarks/results-scale --facts 2000 --no-rerank-compare
```

Trust gates still apply: **contamination_rate must be 0.0**, adversarial leak_rate must be 0.0.
