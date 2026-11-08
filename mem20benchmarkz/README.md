# mem20benchmarkz

Retrieval benchmarks for the mem20 memory engine.

## Corpora

| Name | Size | Command |
|------|------|---------|
| `mem20-agent-kb-v1` | 14 facts / 13 queries | `mem20benchmarkz run` (CI regression) |
| **`mem20-scale-corpus-v2`** (current) | **2,000 records** (700 grounded / 650 ungrounded / 650 false) + 250 probes | `generate-scale` + `run-scale` |
| `mem20-scale-corpus-v3` | **122,178 records** (40,726 each) / 101,090,449 bytes + 600 probes | `benchmarks/v3/build_corpus_v3.py` |
| `mem20-scale-corpus-v1` | 2000 facts / 40 simulated / 140 queries (superseded) | — |

Contamination rate must stay **0.0**. Index drift is a defect to repair, not a product feature.

Latest measured graph (from `benchmarks/results/latest.md`): **654 entities / 3,601 edges**.

## Regression (small)

```bash
mem20benchmarkz run --out benchmarks/results
mem20benchmarkz drift
mem20benchmarkz render benchmarks/results
```

## Scale corpus v2 (2000 entries)

Reference data is cached under `reference/v2/` so generation is offline and deterministic (seed `20261027`).

```bash
# Generate (reproducible bytes)
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2

# Validate invariants
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2

# Run (isolated store, never touches live data)
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes bm25,vector,hybrid,hybrid-rerank-off,graph,keyword,constant \
    --out benchmarks/results
```

Results land in `benchmarks/results/latest.md` and `docs/benchmarks/results-v2.md`.
`benchmarks/results/latest.md` is rendered from `latest.json` by
`benchmarks/render_latest_md.py`; run it with `--check` as a drift gate.

## Trust checks

`run` / `run-scale` exit non-zero if:

- `contamination_rate != 0.0`
- adversarial `leak_rate != 0.0`
- (when reported) `stale_pointer_rate != 0.0`

## License

MIT — same as the monorepo.
