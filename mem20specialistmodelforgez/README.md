# RM-063 — Specialist Model Forge

Outcome: Create small task-specific models and adapters from successful workflows

Breakthrough: The system converts repeated cloud work into cheap local expertise

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `compose` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20specialistmodelforgez --help
python -m mem20specialistmodelforgez simulate
python -m mem20specialistmodelforgez benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20specialistmodelforgez/mem20specialistmodelforgez/tests -q
```
