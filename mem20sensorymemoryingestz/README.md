# RM-024 — Sensory Memory Ingest

Outcome: Turn images, audio, screens, files, and device signals into searchable episodes

Breakthrough: Personal memory extends beyond typed conversations

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `search` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20sensorymemoryingestz --help
python -m mem20sensorymemoryingestz simulate
python -m mem20sensorymemoryingestz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20sensorymemoryingestz/mem20sensorymemoryingestz/tests -q
```
