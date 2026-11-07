# RM-009 — Secure Compute Capsules

Outcome: Execute risky or untrusted tasks in disposable capability-scoped sandboxes

Breakthrough: Any tool can be tried safely with precise resource and data boundaries

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `forecast` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20securecomputecapsulesz --help
python -m mem20securecomputecapsulesz simulate
python -m mem20securecomputecapsulesz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20securecomputecapsulesz/mem20securecomputecapsulesz/tests -q
```
