# RM-095 — Universal Health Nervous System

Outcome: Aggregate deep health, dependency, saturation, and recovery signals in real time

Breakthrough: The system can feel degradation before ordinary uptime checks fail

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `heal` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20universalhealthnervoussystemz --help
python -m mem20universalhealthnervoussystemz simulate
python -m mem20universalhealthnervoussystemz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20universalhealthnervoussystemz/mem20universalhealthnervoussystemz/tests -q
```
