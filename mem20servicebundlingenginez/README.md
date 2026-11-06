# RM-087 — Service Bundling Engine

Outcome: Discover complementary capabilities and package them into higher-value services

Breakthrough: The platform continually creates new combinations customers can buy

Machine-executable local runtime includes versioned state, SQLite WAL persistence, events, SDK CRUD, resumable/idempotent jobs, retries/timeouts/quotas, recovery, `compose` operation logic, decision explanations, feedback, CLI, HTTP console/API, mesh selection/failover, simulator, benchmark, metrics, and opt-in signature mode.

## Run

```bash
# CLI help, then exercise the local runtime end to end
python -m mem20servicebundlingenginez --help
python -m mem20servicebundlingenginez simulate
python -m mem20servicebundlingenginez benchmark
```

## Tests

```bash
PYTHONPATH=/opt/mem20 .venv/bin/python -m pytest mem20servicebundlingenginez/mem20servicebundlingenginez/tests -q
```
