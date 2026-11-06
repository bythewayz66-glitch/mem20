# RM-228 — Style Guide Agent

**Outcome:** Enforce visual, audio, interaction, and narrative style across generated assets in real time

**Breakthrough:** Automated creation preserves a recognizable human-directed identity

This package is the machine-executable local implementation derived from the supplied Off Record Lab roadmap. It includes versioned typed state, SQLite WAL persistence, event history/snapshots, SDK CRUD/subscription, resumable idempotent jobs, cancellation, retries/timeouts/quotas/backpressure, deterministic replica reconciliation, local/hybrid/cloud placement/failover, roadmap-specific `ingest` logic, decision confidence/explanations, feedback, CLI, HTTP console/API, safety guards, simulator, benchmark/metrics, and rollback-capable installer.

Named live product surfaces, real provider/device credentials, production traffic, and governed FreeStack deployment remain target-environment integration and are not claimed complete.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20styleguideagentz --help
python -m mem20styleguideagentz simulate
python -m mem20styleguideagentz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20styleguideagentz/mem20styleguideagentz/tests -q
```
