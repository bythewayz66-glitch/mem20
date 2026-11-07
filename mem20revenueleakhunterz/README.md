# RM-089 — Revenue Leak Hunter

Outcome: Detect churn risks, failed handoffs, underbilling, unused entitlements, and broken conversion paths

Breakthrough: Hidden losses become actionable software events

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `forecast` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20revenueleakhunterz --help
python -m mem20revenueleakhunterz simulate
python -m mem20revenueleakhunterz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20revenueleakhunterz/mem20revenueleakhunterz/tests -q
```
