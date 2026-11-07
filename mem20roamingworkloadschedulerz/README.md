# RM-044 — Roaming Workload Scheduler

Outcome: Move active jobs between devices as connectivity, cost, and performance change

Breakthrough: Long-running work follows the best available hardware

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `simulate` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20roamingworkloadschedulerz --help
python -m mem20roamingworkloadschedulerz simulate
python -m mem20roamingworkloadschedulerz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20roamingworkloadschedulerz/mem20roamingworkloadschedulerz/tests -q
```
