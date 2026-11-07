# RM-085 — Resource Exchange Market

Outcome: Match internal and external demand with available people, agents, compute, and inventory

Breakthrough: Unused capacity becomes productive automatically

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `match` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20resourceexchangemarketz --help
python -m mem20resourceexchangemarketz simulate
python -m mem20resourceexchangemarketz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20resourceexchangemarketz/mem20resourceexchangemarketz/tests -q
```
