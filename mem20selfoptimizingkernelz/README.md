# RM-007 — Self-Optimizing Kernel

Outcome: Continuously tune workload placement, caches, queues, and process limits from observed demand

Breakthrough: The platform automatically becomes faster and cheaper over time

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `optimize` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20selfoptimizingkernelz --help
python -m mem20selfoptimizingkernelz simulate
python -m mem20selfoptimizingkernelz benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20selfoptimizingkernelz/mem20selfoptimizingkernelz/tests -q
```
