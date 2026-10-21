# mem20benchmarkz

Retrieval benchmarks for the mem20 memory engine.

## Corpora

| Name | Size | Command |
|------|------|---------|
| `mem20-agent-kb-v1` | 14 facts / 13 queries | `mem20benchmarkz run` (CI regression) |
| `mem20-scale-corpus-v1` | **2000** facts / 40 simulated / 140 queries | `generate-scale` + `run-scale` |

Contamination rate must stay **0.0**. Index drift is a defect to repair, not a product feature.

## Regression (small)

```bash
mem20benchmarkz run --out benchmarks/results
mem20benchmarkz drift
mem20benchmarkz render benchmarks/results
```

## Scale (2000 entries)

Generate the corpus (deterministic, seed 20 — not committed as a blob):

```bash
mem20benchmarkz generate-scale --out benchmarks/corpora/mem20-scale-corpus-v1
```

Ingest once, then score:

```bash
mem20benchmarkz ingest-scale \
  --corpus benchmarks/corpora/mem20-scale-corpus-v1 \
  --store /tmp/mem20-scale-store \
  --progress

mem20benchmarkz run-scale \
  --store /tmp/mem20-scale-store \
  --corpus benchmarks/corpora/mem20-scale-corpus-v1 \
  --out benchmarks/results-scale \
  --no-rerank-compare
```

All-in-one (temp store, in-memory 2000 facts):

```bash
mem20benchmarkz run-scale --facts 2000 --out benchmarks/results-scale --no-rerank-compare
```

## Trust checks

`run` / `run-scale` exit non-zero if:

- `contamination_rate != 0.0`
- adversarial `leak_rate != 0.0`
- (when reported) `stale_pointer_rate != 0.0`

## License

MIT — same as the monorepo.
