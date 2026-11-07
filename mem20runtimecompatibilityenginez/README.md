# RM-097 — Runtime Compatibility Engine

Outcome: Predict whether modules, schemas, and interfaces can operate together before installation

Breakthrough: Dependency conflicts are blocked before they become outages

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `forecast` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20runtimecompatibilityenginez --help
python -m mem20runtimecompatibilityenginez simulate
python -m mem20runtimecompatibilityenginez benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20runtimecompatibilityenginez/mem20runtimecompatibilityenginez/tests -q
```
