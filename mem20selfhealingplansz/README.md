# RM-055 — Self-Healing Plans

Outcome: Detect plan drift and rebuild only the damaged portion of an execution graph

Breakthrough: Long missions survive changing conditions and partial failures

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `heal` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20selfhealingplansz --help
python -m mem20selfhealingplansz simulate
python -m mem20selfhealingplansz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20selfhealingplansz/mem20selfhealingplansz/tests -q
```
