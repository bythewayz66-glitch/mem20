# RM-071 — Universal Integration Compiler

Outcome: Compile API descriptions, examples, and observed traffic into working typed connectors

Breakthrough: New integrations can be created in hours instead of weeks

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `route` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20universalintegrationcompilerz --help
python -m mem20universalintegrationcompilerz simulate
python -m mem20universalintegrationcompilerz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20universalintegrationcompilerz/mem20universalintegrationcompilerz/tests -q
```
