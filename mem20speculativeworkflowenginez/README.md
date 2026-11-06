# RM-053 — Speculative Workflow Engine

Outcome: Run low-cost branches ahead of time and commit the best valid path

Breakthrough: Complex work accelerates through controlled parallel futures

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `analyze` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20speculativeworkflowenginez --help
python -m mem20speculativeworkflowenginez simulate
python -m mem20speculativeworkflowenginez benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20speculativeworkflowenginez/mem20speculativeworkflowenginez/tests -q
```
