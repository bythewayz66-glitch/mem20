# Benchmark corpora

| Corpus | Size | Purpose |
|--------|------|---------|
| `mem20-agent-kb-v1` | 14 facts / 13 queries | CI regression gate (in `corpus.py`) |
| **`mem20-scale-corpus-v2`** (current) | **2,000 records** (700 grounded / 650 ungrounded / 650 false) + 250 probes | Scale latency + trust + adversarial |
| `mem20-scale-corpus-v1` | 2000 facts / 40 simulated / 140 queries | Superseded by v2 |

## Generate the 2000-entry scale corpus (v2)

Nothing large is committed. Generate deterministically (seed `20261027`):

```bash
mem20benchmarkz generate-scale --out /tmp/mem20-scale-corpus-v2
mem20benchmarkz validate-scale /tmp/mem20-scale-corpus-v2
```

Reference data lives under `reference/v2/` (offline cache).

Produces:

- `records.jsonl` — 2,000 labelled records  
- `queries.jsonl` — 250 probes (direct / multi / adversarial / adversarial_hard / contradiction / unanswerable)  
- `manifest.json`

## Ingest + run

```bash
mem20benchmarkz run-scale --corpus /tmp/mem20-scale-corpus-v2 --bulk \
    --modes keyword,semantic --out benchmarks/results
```

Trust gates still apply: **contamination_rate must be 0.0**, adversarial leak_rate must be 0.0.

Latest measured graph: **654 entities / 3,601 edges** (see `benchmarks/results/latest.md`).
