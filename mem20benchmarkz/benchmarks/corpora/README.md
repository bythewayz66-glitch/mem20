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

Reference data lives under `reference/v2/` (offline cache). **The cache is not
committed** — only its `README.md` is. On a clean clone `generate-scale` fails
with `FileNotFoundError: missing cached reference data` until the three files are
fetched:

```bash
mkdir -p reference/v2
curl -sL -o reference/v2/periodic-table.json https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json
curl -sL -o reference/v2/iso-3166.json https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.json
curl -sL -o reference/v2/mime-db.json https://raw.githubusercontent.com/jshttp/mime-db/master/db.json
```

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
