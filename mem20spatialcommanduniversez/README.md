# RM-216 — Spatial Command Universe

**Outcome:** Represent projects, runtimes, agents, data, and live operations as interactive spatial environments

**Breakthrough:** Users can walk through and manipulate complex software systems

This package is the machine-executable local implementation derived from the supplied Off Record Lab roadmap. It includes versioned typed state, SQLite WAL persistence, event history/snapshots, SDK CRUD/subscription, resumable idempotent jobs, cancellation, retries/timeouts/quotas/backpressure, deterministic replica reconciliation, local/hybrid/cloud placement/failover, roadmap-specific `analyze` logic, decision confidence/explanations, feedback, CLI, HTTP console/API, safety guards, simulator, benchmark/metrics, and rollback-capable installer.

Named live product surfaces, real provider/device credentials, production traffic, and governed FreeStack deployment remain target-environment integration and are not claimed complete.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20spatialcommanduniversez --help
python -m mem20spatialcommanduniversez simulate
python -m mem20spatialcommanduniversez benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20spatialcommanduniversez/mem20spatialcommanduniversez/tests -q
```
